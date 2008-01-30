#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Version: 1.5.5
#

import sys

import time
import pprint
import traceback
import types

from cgi import escape
import omniORB

# DNS lib imports
import dns.message
import dns.resolver
import dns.query

import config

# CherryPy main import
import cherrypy
#cherrypy.session = cherrypy.session # to pylint stop abuse :)

# decorator for exposing methods
import exposed

# CORBA objects
from corba import Corba, CorbaServerDisconnectedException
corba = Corba()

# recoder of CORBA objects
from corbarecoder import CorbaRecode
recoder = CorbaRecode('utf-8')
c2u = recoder.decode # recode from corba string to unicode
u2c = recoder.encode # recode from unicode to strings

# XML formatter / BeautifulSoup
try:
    from BeautifulSoup import BeautifulStoneSoup
    def prettify(xml):
        soup = BeautifulStoneSoup(xml)
        return soup.prettify()
except ImportError:
    def uglify(xml):
        return '\n'.join('\n<'.join('>\n'.join(xml.split('>')).split('<')).split('\n\n'))
    prettify = uglify # :-)

from translation import _


from webwidgets.templates import BaseSite, BaseSiteMenu, LoginPage, DisconnectedPage, FilterPage, DomainsDetail, RegistrarsDetail
from webwidgets.gpyweb.gpyweb import WebWidget
from webwidgets.gpyweb.gpyweb import DictLookup, attr, ul, li, a, div, span, p
from webwidgets.utils import isiterable
from webwidgets.menu import MenuHoriz
from menunode import menu_tree
from webwidgets.adifforms import *

from itertable import IterTable, fileGenerator


class AdifError(Exception):
    pass
class IorNotFoundError(AdifError):
    pass
class MenuDoesNotExistsError(AdifError):
    def __init__(self, menu_handle):
        super(MenuDoesNotExistsError, self).__init__()
        self.menu_handle = menu_handle
    def __str__(self):
        return 'Menu with handle "%s" does not exists!' % self.menu_handle
    def __unicode__(self):
        return self.__str__()

# decorator for login-required pages
def protectedPage(fn):
    def _wrapper(*args, **kwd):
        if cherrypy.session.get('user', None):
            return fn(*args, **kwd)
        redir_addr = '/login/?next=%s' % cherrypy.request.path_info
        if cherrypy.request.query_string:
            redir_addr += '?' + cherrypy.request.query_string
        raise cherrypy.HTTPRedirect(redir_addr)
    return _wrapper

def protectedPageNP(fn, nperms, nperm_type='all'):
    def _wrapper(*args, **kwd):
        user = cherrypy.session.get('user', None)
        if user:
            if not user.check_nperms(nperms, nperm_type):
                return fn(*args, **kwd)
            else:
                context = {}
                context['main'] = _('You have not permissions for this')
                if config.debug:
                    context['main'] += ' usernperm = %s, nperms=%s, nperm_type=%s' % (user.perms, nperms, nperm_type)
                return BaseSiteMenu(context)
        raise cherrypy.HTTPRedirect('/login/?next=%s' % cherrypy.request.path_info + '?' + cherrypy.request.query_string)



class User(object):
    def __init__(self, login):
        self.login = login
        # negative permissions or forbiddance 
#        self.nperms = ['domain.read', 'domain.create', 'domain.change', 'domain.delete',
#                       'contact.read', 'contact.create', 'contact.change', 'contact.delete',
#                       'nsset.read', 'nsset.create', 'nsset.change', 'nsset.delete',
#                       'registrar.read', 'registrar.create', 'registrar.change', 'registrar.delete',
#                      ]
        #self.nperms = ['domains.read', 'contacts.read', 'nssets.read']
        self.nperms = ['domains.filter.owner', 'domains.filter.email']
        print 'vytvoren user s nperms = ', str(self.nperms)
        
    def has_nperm(self, nperm):
        return nperm in self.nperms
    
    def has_all_nperms(self, nperms):
        for nperm in nperms:
            if nperm not in self.nperms:
                return False
        return True
    
    def has_one_nperms(self, nperms):
        if not nperms:
            return True
        else:
            for nperm in nperms:
                if nperm in self.nperms:
                    return True
            return False

    def check_nperms(self, nperms, nperm_type = 'all'):
        'Returns True if user has NOT permmission (has negative permission)'
        #print 'USER NPERM pri checku: %s, proti %s, check_type %s' % (self.nperms, nperms, nperm_type),  
        result = ((isinstance(nperms, types.StringTypes) and self.has_nperm(nperms)) or 
                (isiterable(nperms) and 
                     (nperm_type == 'all' and self.has_all_nperms(nperms) or
                      nperm_type == 'one' and self.has_one_nperms(nperms))
                )
               )
        #print ' -> %s' % result
        return result 


class ListTableMixin(object):

    __metaclass__ = exposed.exposed

    def _get_list(self, context, cleaned_filters=None, **kwd):
        key = cherrypy.session.get('corbaSession', '')
        size = config.tablesize
        try:
            table = IterTable(self.classname, key, size)
        except CorbaServerDisconnectedException:
            self._disconnected()
        try:
            page = int(kwd.get('page', 1))
        except ValueError:
            page = 1
        
        #[ filters.__setitem__(x[7:], kwd[x]) for x in kwd if x.startswith('filter_') ]
        if cleaned_filters:
            table.clear_filter()
            table.set_filter(cleaned_filters)
        if kwd.get('cf'):
            table.clear_filter()
        if kwd.get('reload'):
            table.reload()
        if kwd.get('load'): # load current filter from backend
            cleaned_filter_data = table.get_filter_data()
            form_class = self._get_form_class()
            form = UnionFilterForm(cleaned_filter_data, form_class=form_class, data_cleaned=True)
            context['form'] = form
            context['main'].add('kwd_json_data_loaded:', cleaned_filter_data)
        if kwd.get('list_all'):
            table.clear_filter()
            table._table.add()
            table.reload()

        if table.num_rows == 0:
            context['main'].add(_("No_entries_found"))
        if table.num_rows == 1:
            rowId = table.get_row_id(0)
            raise cherrypy.HTTPRedirect('/%s/detail/?id=%s' % (self.classname, rowId))
        if kwd.get('txt', None):
            cherrypy.response.headers["Content-Type"] = "text/plain"
            cherrypy.response.headers["Content-Disposition"] = "inline; filename=%s_%s.txt" % (self.classname, time.strftime('%Y-%m-%d'))
            return fileGenerator(table)
        elif kwd.get('csv', None):
            cherrypy.response.headers["Content-Type"] = "application/vnd.ms-excel"
            cherrypy.response.headers["Content-Disposition"] = "attachement; filename=%s_%s.csv" % (self.classname, time.strftime('%Y-%m-%d'))
            return fileGenerator(table)
        table.set_page(page)
        
        context['itertable'] = table
        return context
    
    @protectedPage
    def filter(self, **kwd):
        if kwd:
            print 'prisla data %s' % kwd
        
        context = {'main': div()}

        if kwd.get('cf') or kwd.get('page') or kwd.get('load') or kwd.get('list_all'): # clear filter - whole list of objects without using filter form
            context = self._get_list(context, **kwd)
        else:
            form_class = self._get_form_class()
            # bound form with data
            if kwd.has_key('json_data'):
                print 'posilam data %s' % kwd
                form = UnionFilterForm(kwd, form_class=form_class)
            else:
                form = UnionFilterForm(form_class=form_class)
            context['form'] = form
            if form.is_bound:
                context['main'].add(p(u'kwd:' + unicode(kwd)))
            if form.is_valid():
                context['main'].add(u'<br />Jsem validni<br />')
                context['main'].add(u'cleaned_data:' + unicode(form.cleaned_data) + '<br />')
                print u'cleaned_data:' + unicode(form.cleaned_data)
                context = self._get_list(context, form.cleaned_data, **kwd)
                return self._render('filter', context)
            else:
                
                if form.is_bound:
                    context['main'].add(u'Jsem nevalidni, errors:' + unicode(form.errors.items()))
                    context['headline'] = '%s filter' % self.__class__.__name__
        
        return self._render('filter', context)

    def _get_form_class(self):
        form_name = self.__class__.__name__ + 'FilterForm'
        form_class = getattr(sys.modules[self.__module__], form_name, None)
        if not form_class:
            raise RuntimeError('No such formclass in modules "%s"' % form_name)
        return form_class

    @protectedPage
    def index(self):
        raise cherrypy.HTTPRedirect('/%s/filter/' % (self.classname))


class Page(object):

    __metaclass__ = exposed.exposed

    def __init__(self):
        super(Page, self).__init__()

    def index(self):
        """index page, similiar to index.php, index.html and so on"""

    def default(self, *params, **kwd):
        """catch-all for any non-defined method"""
        return '%s,%s,%s' % (self.__class__, params, kwd)

class AdifPage(Page):

    def __init__(self):
        Page.__init__(self)
        self.classname = self.__class__.__name__.lower()
        self.menu_tree = menu_tree
        #self.encoding = 'utf-8'
        #self.page = self._template('layout')
        #self.navigation = self._template('navigation')
        #self.status = self._template('status')
        #self.macros = self._template('macros').macros
        #self.corba_server_name = None
        #self.admin = None
        #self.mailer = None
        #self.filemanager = None

        self.__defaults__()

    def __defaults__(self):
        pass
        #self.here = {}
        #self.here['page'] = {}
        #self.here['page']['sidebar'] = self.navigation
        #self.here['page']['status'] = self.status
        #self.here['page']['title'] = cfg.get('html', 'title')
        #self.here['macros'] = self.macros

    def _template(self, action = ''):
        if action == 'base':
            return BaseSiteMenu
        if action == 'login':
            return LoginPage
        elif action == 'filter':
            return FilterPage
        elif action == 'disconnected':
            return DisconnectedPage
        else:
            # returns ClassName + Action (e.g. DomainsDetail) class from module of this class, if there is no such, then it returns BaseSiteMenu: 
            template_name = self.__class__.__name__ + action.capitalize()
            template = getattr(sys.modules[self.__module__], template_name, None)
            if template is None:
                print "TEMPLATE %s IN MODULE %s NOT FOUND, USING DEFAULT: BaseSiteMenu" % (template_name, sys.modules[self.__module__])
                template = BaseSiteMenu 
            if not issubclass(template, WebWidget):
                raise RuntimeError('%s is not derived from WebWidget - it cannot be template!' % repr(template))
            return template
            

        
        
    def _get_menu(self, action):
        return MenuHoriz(self.menu_tree, self._get_menu_handle(action), cherrypy.session['user'])
    
    def _get_menu_handle(self, action):
        if action in ('filter', 'create') and self.classname not in ('domains', 'contacts', 'nssets'):
            return self.classname + action
        else:
            return self.classname

    def _get_selected_menu_body_id(self, action):
        handle = self._get_menu_handle(action)
        menu_node = self.menu_tree.get_menu_by_handle(handle)
        if menu_node is None:
            raise MenuDoesNotExistsError(handle)
        return menu_node.body_id
    
    def _render(self, action='', ctx=None):
        context = DictLookup()
        context.approot = '/'
        context.classname = self.classname
        context.classroot = "%s%s/" % (context.approot, context.classname)
        context.corba_server = cherrypy.session.get('corba_server_name')
        context.request = cherrypy.request
        
        user = cherrypy.session.get('user', None)
        if user: 
            context.user = user 
            context.menu = self._get_menu(action) or None # Login page has no menu
            context.body_id = self._get_selected_menu_body_id(action)
        
        if ctx:
            context.update(ctx)
        
        temp_class = self._template(action)(context)
        print u"BERU TEMPLARU:%s" % repr(temp_class)
        #import pdb; pdb.set_trace()
        result = temp_class.render()
        
        return result

    def _registrars(self):
        registrars = c2u(cherrypy.session.get('Admin').getRegistrars())
        return registrars

    def _countries(self):
        default = c2u(cherrypy.session.get('Admin').getDefaultCountry())
        countries = [ {'cc': country.cc, 'name': country.name, 'default': country.cc == default and "selected" or ""} for country in c2u(cherrypy.session.get('Admin').getCountryDescList()) ]
        return countries

    def _eppActionList(self):
        actionlist = c2u(cherrypy.session.get('Admin').getEPPActionTypeList())
        return actionlist

    def _invoiceTypeList(self):
        typelist = [ {'id': x[0], 'type': x[1]['type']} for x in enumerate(corba.module.Invoicing.Invoices) ]
        return typelist

    def _mailTypes(self):
        mailtypes = c2u(cherrypy.session.get('Mailer').getMailTypes())
        return mailtypes

    def default(self, *params, **kwd):
        raise cherrypy.HTTPRedirect('/%s' % (self.classname))
#        return "%s<br />%s" % (str(params), str(kwd))

    def _disconnected(self):
        cherrypy.session['user'] = False
        cherrypy.session['corbaSession'] = None
        raise cherrypy.HTTPRedirect('/disconnected')

    @protectedPage
    def index(self):
        #html = self._template('index', self.classname)
        #here = self.here.copy()
        #here['page']['content'] = html
        return self._render()

class ADIF(AdifPage):

    def __init__(self):
        AdifPage.__init__(self)
    
    def _get_menu_handle(self, action):
        return 'summary'
    
    @protectedPage
    def index(self):
        if cherrypy.session.get('user'):
            raise cherrypy.HTTPRedirect('/summary/')
        else:
            raise cherrypy.HTTPRedirect('/login/')
        
    def login(self, *args, **kwd):
        
        #html = self._template('index', self.classname)
        #here = self.here.copy()
        #here['page']['content'] = html
        if kwd:
            if cherrypy.request.method == 'GET' and kwd.get('next'):
                form = LoginForm(action='/login/', method='post')
                form.fields['next'].initial = kwd['next']
            else:
                form = LoginForm(kwd, action='/login/', method='post')
        else:
            form = LoginForm(action='/login/', method='post')
            
        if form.is_valid():
            print 'form is valid'
            login = form.cleaned_data.get('login', '')    
            password = form.cleaned_data.get('password', '')
            corba_server = int(form.cleaned_data.get('corba_server', 0))
            try:
                ior=config.iors[corba_server]
                corba.connect(ior)
                admin = corba.getObject('fred', 'Admin', 'Admin')
                corbaSession = admin.login(u2c(login), u2c(password))
                cherrypy.session['corbaSession'] = corbaSession
                
                cherrypy.session['user'] = User(login) #XXX to tu nebude, to vrati korba
                
                cherrypy.session['corba_server_name'] = form.fields['corba_server'].choices[corba_server][1]
                cherrypy.session['Admin'] = admin
#                cherrypy.session['Mailer'] = corba.getObject('fred', 'Mailer', 'Mailer')
#                cherrypy.session['FileManager'] = corba.getObject('fred', 'FileManager', 'FileManager')


                raise cherrypy.HTTPRedirect(form.cleaned_data.get('next'))
            except omniORB.CORBA.BAD_PARAM, e:
                form.non_field_errors().append(_('Bad corba call! ') + '(%s)' % (str(e)))
                if config.debug:
                    form.non_field_errors().append(escape(unicode(traceback.format_exc())).replace('\n', '<br/>'))
            except corba.module.Admin.AuthFailed, e:
                form.non_field_errors().append(_('Login error, please enter correct login and password'))
                if config.debug:
                    form.non_field_errors().append('(type: %s, exception: %s)' % (escape(unicode(type(e))), unicode(e)))
                    form.non_field_errors().append(escape(unicode(traceback.format_exc())).replace('\n', '<br/>'))

        form.action = '/login/'
        return self._render('login', {'form': form})
        
        
        
    def logout(self):
        cherrypy.session['user'] = False
        cherrypy.session['corbaSession'] = None
        cherrypy.session['corba_server_name'] = None
        cherrypy.session['Admin'] = None
        cherrypy.session['Mailer'] = None
        cherrypy.session['FileManager'] = None
        raise cherrypy.HTTPRedirect('/')

    def disconnected(self):
        if not cherrypy.session.get('corbaSession', None):
            #html = self._template('disconnected', self.classname)
            #here = self.here.copy()
            #here['page']['content'] = html
            return self._render('disconnected')
        else:
            raise cherrypy.HTTPRedirect('/')


class Summary(AdifPage):
    def _template(self, action=''):
        if action == 'summary':
            return BaseSiteMenu
        else:
            return BaseSiteMenu
        
    @protectedPage
    def index(self):
        context = DictLookup()
        context.main = ul(
            li(a(attr(href='/naky_url/'), u'ňáká nabídka')),
        )
        return self._render(ctx=context)
    
class Logs(AdifPage):
    def _template(self, action=''):
        return BaseSiteMenu
        
    @protectedPage
    def index(self):
        context = DictLookup()
        context.main = p('Tady asi nic nebude, pokud jo, tak asi registrar/filter, a tim padem by tahle klasa Logs byla zbytecna')
        return self._render('base', ctx=context)

class Statistics(AdifPage):
    def _template(self, action=''):
        return BaseSiteMenu

class Registrars(AdifPage, ListTableMixin):

    def __init__(self):
        AdifPage.__init__(self)
        ListTableMixin.__init__(self)
    
    @protectedPage
    def detail(self, **kwd):
        context = {}
        create = kwd.get('new')
        if create: 
            new = []
            new.append(0) # id
            new.extend(*[['']*14])
            new.append(0) # money
            new.append([])
            new.append(0) # hidden 
            result = corba.module.Registrar(*new) # empty registrar
#            print result
        else:
            handle = kwd.get('handle', None)
            admin = cherrypy.session.get('Admin')
            func = admin.getRegistrarByHandle 
            if not handle:
                try:
                    handle = int(kwd.get('id', None))
                except (TypeError, ValueError):
                    context['main'] = _("Required_integer_as_parameter")
                    return self._render('base', ctx=context)
                func = admin.getRegistrarById
            if not handle:
                raise cherrypy.HTTPRedirect('/%s/list' % (self.classname))
            try:
                result = c2u(func(u2c(handle)))
            except (corba.module.Admin.ObjectNotFound,):
                context['main'] = _("Object_not_found")
                return self._render('base', ctx=context)
        
        context['edit'] = kwd.get('edit', False)
        context['result'] = result
        context['utils'] = {}
        context['utils']['countries'] = self._countries()
        context['utils']['certCount'] = len(result.access)
        return self._render('detail', context)

    @protectedPage
    def edit(self, *params, **kwd):
        kwd['edit'] = True
        return self.detail(*params, **kwd)

    @protectedPage
    def create(self, *params, **kwd):
        kwd['edit'] = True
        kwd['new'] = True
        return self.detail(*params, **kwd)

    @protectedPage
    def modify(self, **kwd):
        k = ['id', 'handle', 'name', 'organization', 'street1', 'street2', 
            'street3', 'city', 'stateorprovince', 'postalcode', 'country', 
            'telephone', 'fax', 'email', 'url', 'credit']
        v = []
        try:
            for key in k:
                v.append(kwd[key])
        except (KeyError,):
            return _("Incorrect_parameter_count")
        v[0] = int(kwd['id']) # id
        v[15] = '' # credit
        # certificates
        certificates = []
        passwords = [ x.replace('password', '') for x in kwd.keys() if x.startswith('password') ]
        for i in passwords:
            passwd = kwd['password%s' % i]
            md5cert = kwd['md5Cert%s' % i]
            account = corba.module.EPPAccess(passwd, md5cert)
            certificates.append(account)
        v.append(certificates)
        v.append(0) # XXX hack Registrar.hidden
        reg = corba.module.Registrar(*v)
        try:
            cherrypy.session.get('Admin').putRegistrar(reg)
        except corba.module.Admin.UpdateFailed:
            context = {}
            context['main'] = _("Saving_failed")
            return self._render('modify', context)
        raise cherrypy.HTTPRedirect('/%s/list/?reload=1' % (self.classname))

class Requests(AdifPage, ListTableMixin):

    def __init__(self):
        AdifPage.__init__(self)
        ListTableMixin.__init__(self)

    @protectedPage
    def detail(self, **kwd):
        context = {}
        admin = cherrypy.session.get('Admin') 
        handle = kwd.get('svTRID', None)
        func = admin.getEPPActionBySvTRID
        if not handle:
            try:
                handle = int(kwd.get('id', None))
            except (TypeError, ValueError):
                context['main'] = _("Required_integer_as_parameter")
                return self._render('base', ctx=context)
            func = admin.getEPPActionById
        if not handle:
            raise cherrypy.HTTPRedirect('/%s/list/' % (self.classname))
        try:
            result = c2u(func(u2c(handle)))
        except (corba.module.Admin.ObjectNotFound,):
            context['main'] = _("Object_not_found")
            return self._render('base', ctx=context)

        if result.registrarHandle:
            result.registrar = c2u(cherrypy.session.get('Admin').getRegistrarByHandle(result.registrarHandle))
        result.xml = prettify(result.xml)
        context['result'] = result
        return self._render('detail', context)
            

class Domains(AdifPage, ListTableMixin):

    def __init__(self):
        AdifPage.__init__(self)
        ListTableMixin.__init__(self)
        
    @protectedPage
    def detail(self, **kwd):
        context = {}
        create = kwd.get('new')

        if create:
            result = corba.module.Domain(0, *['']*14) # empty Domain
        else:
            admin = cherrypy.session.get('Admin')
            handle = kwd.get('handle', None)
            func = admin.getDomainByFQDN
            if not handle:
                try:
                    handle = int(kwd.get('id', None))
                except (TypeError, ValueError):
                    context['main'] = _("Non_numeric_ID")
                    return self._render('detail', context)
                func = admin.getDomainById
#            if not handle:
#                raise cherrypy.HTTPRedirect('/%s/list' % (self.classname))
            try:
                result = c2u(func(u2c(handle)))
            except (corba.module.Admin.ObjectNotFound,):
                context['main'] = _("Object_not_found")
                return self._render('detail', context)
            else:
                result.registrant = c2u(admin.getContactByHandle(u2c(result.registrantHandle)))
                if result.nssetHandle:
                    nsset = c2u(admin.getNSSetByHandle(u2c(result.nssetHandle)))
                    techs = []
                    for tech in nsset.admins:
                        techs.append(c2u(admin.getContactByHandle(u2c(tech))))
                    nsset.admins = techs
                    result.__dict__['nsset'] = nsset
                adm = []
                for admin_handle in result.admins:
                    adm.append(c2u(admin.getContactByHandle(u2c(admin_handle))))
                result.admins = adm
                adm = []
                for admin_handle in result.temps:
                    adm.append(c2u(admin.getContactByHandle(u2c(admin_handle))))
                result.temps = adm
                if result.createRegistrarHandle:
                    #import pdb; pdb.set_trace()
                    print "HANDLE", result.createRegistrarHandle
                    res = admin.getRegistrarByHandle(u2c(result.createRegistrarHandle))
                    result.createRegistrar = c2u(res)
                if result.updateRegistrarHandle:
                    result.updateRegistrar = c2u(admin.getRegistrarByHandle(u2c(result.updateRegistrarHandle)))
                if result.registrarHandle:
                    result.registrar = c2u(admin.getRegistrarByHandle(u2c(result.registrarHandle)))
        
        context['edit'] = kwd.get('edit')
        
        print "RESULT", result
        context['result'] = (repr(result)) or "bez vysledku"
        return self._render('detail', context)

    @protectedPage
    def dig(self, **kwd):
        context = {}
        handle = kwd.get('handle', None)
        if not handle:
            raise cherrypy.HTTPRedirect('/%s/list/' % (self.classname))
        try:
            query = dns.message.make_query(handle, 'ANY')
            resolver = dns.resolver.get_default_resolver().nameservers[0]
            dig = c2u(dns.query.udp(query, resolver).to_text())
        except:
            context['main'] = _("Object_not_found")
            return self._render('base', ctx=context)
        context['result'] = {}
        context['result']['handle'] = handle
        context['result']['dig'] = dig
        return self._render('dig', context)
        

class Contacts(AdifPage, ListTableMixin):

    def __init__(self):
        AdifPage.__init__(self)
        ListTableMixin.__init__(self)

    @protectedPage
    def detail(self, **kwd):
        context = {}
        create = kwd.get('new')
        if create: 
            result = corba.module.Contact(0, *['']*32) # empty Contact
        else:
            admin = cherrypy.session.get('Admin')
            handle = kwd.get('handle', None)
            func = admin.getContactByHandle
            if not handle:
                try:
                    handle = int(kwd.get('id', None))
                except (TypeError, ValueError):
                    context['main'] = _("Required_integer_as_parameter")
                    return self._render('base', ctx=context)
                func = admin.getContactById
            if not handle:
                raise cherrypy.HTTPRedirect('/%s/list' % (self.classname))
            try:
                result = c2u(func(u2c(handle)))
            except (corba.module.Admin.ObjectNotFound,):
                context['main'] = _("Object_not_found")
                return self._render('base', ctx=context)
            # XXX: HACK
            # convert all disclose* properties to: 0 -> False, 1 -> True
            [ result.__dict__.__setitem__(x, [False, True][result.__dict__[x]]) for x in result.__dict__ if x.startswith('disclose') ]
        
        context['edit'] = kwd.get('edit')
        context['result'] = result
        return self._render('detail', context)


class NSSets(AdifPage, ListTableMixin):

    def __init__(self):
        AdifPage.__init__(self)
        ListTableMixin.__init__(self)

    @protectedPage
    def detail(self, **kwd):
        context = {}
        create = kwd.get('new') 
        if create: 
            result = corba.module.NSSet(0, *['']*11) # empty NSSet
        else:
            admin = cherrypy.session.get('Admin')
            handle = kwd.get('handle', None)
            func = admin.getNSSetByHandle
            if not handle:
                try:
                    handle = int(kwd.get('id', None))
                except (TypeError, ValueError):
                    context['main'] = _("Required_integer_as_parameter")
                    return self._render('base', ctx=context)
                func = admin.getNSSetById
            if not handle:
                raise cherrypy.HTTPRedirect('/%s/list' % (self.classname))
            try:
                result = c2u(func(u2c(handle)))
            except (corba.module.Admin.ObjectNotFound,):
                context['main'] = _("Object_not_found")
                return self._render('base', ctx=context)
            else:
                techs = []
                for tech in result.admins:
                    techs.append(c2u(admin.getContactByHandle(tech)))
                result.admins = techs
                if result.createRegistrarHandle:
                    result.createRegistrar = c2u(admin.getRegistrarByHandle(result.createRegistrarHandle))
                if result.updateRegistrarHandle:
                    result.updateRegistrar = c2u(admin.getRegistrarByHandle(result.updateRegistrarHandle))
                if result.registrarHandle:
                    result.registrar = c2u(admin.getRegistrarByHandle(result.registrarHandle))

        context['edit'] = kwd.get('edit')
        context['result'] = result
        return self._render('detail', context)

class Mails(AdifPage, ListTableMixin):

    def __init__(self):
        AdifPage.__init__(self)
        ListTableMixin.__init__(self)

    def _rehashHandles(self, handles):
        hmap = {'HT_DOMAIN': 'domains',
                'HT_CONTACT': 'contacts',
                'HT_NSSET': 'nssets',
                'HT_REGISTRAR': 'registrars'}
        handles = [ {'type': hmap.get(cherrypy.session.get('Admin').checkHandle(u2c(handle))[0].hType._n), 'handle': handle} for handle in handles ]
        return handles

    def _rehashAttachments(self, attachments):
        new = []
        for attId in attachments:
            try:
                new.append(c2u(cherrypy.session.get('FileManager').info(attId)))
            except corba.module.FileManager.IdNotFound:
                new.append({'name': 'ERROR-ATTACHMENT-ID:%s' % attId})
        return new

    @protectedPage
    def detail(self, **kwd):
        context = {}
        create = kwd.get('create')
        if not create:
            admin = cherrypy.session.get('Admin')
            try:
                handle = int(kwd.get('id', None))
            except (TypeError, ValueError):
                context['main'] = _("Required_integer_as_parameter")
                return self._render('base', ctx=context)
            func = admin.getEmailById
            try:
                result = c2u(func(u2c(handle)))
            except (corba.module.Admin.ObjectNotFound,):
                context['main'] = _("Object_not_found")
                return self._render('base', ctx=context)
        mtype = [ x.name for x in self._mailTypes() if x.id == result.type ]
        if len(mtype) == 1:
            result.type = mtype[0]
        else:
            result.type = 'unknown'
        result.handles = self._rehashHandles(result.handles)
        result.attachments = self._rehashAttachments(result.attachments)
        context['result'] = result
        return self._render('detail', context)

    @protectedPage
    def attachment(self, **kwd):
        context = {}
        try:
            handle = int(kwd.get('id', None))
        except (TypeError, ValueError):
            context['main'] = _("Required_integer_as_parameter")
            return self._render('base', ctx=context)
        if handle:
            response = cherrypy.response
            filemanager = cherrypy.session.get('FileManager')
            info = filemanager.info(u2c(handle))
            response.headers['Content-Type'] = info.mimetype
            cd = "%s; filename=%s" % ('attachment', info.name)
            response.headers["Content-Disposition"] = cd
            response.headers['Content-Length'] = info.size
            f = filemanager.load(u2c(handle))
            body = ""
            while 1:
                part = f.download(102400) # 100kBytes
                if part:
                    body = "%s%s" % (body, part)
                else:
                    break
            response.body = body
            return response.body

class AuthInfos(AdifPage, ListTableMixin):

    def __init__(self):
        AdifPage.__init__(self)
        ListTableMixin.__init__(self)

    @protectedPage
    def detail(self, **kwd):
        context = {}
        try:
            handle = int(kwd.get('id', None))
        except (TypeError, ValueError):
            context['main'] = _("Required_integer_as_parameter")
            return self._render('base', ctx=context)
        func = cherrypy.session.get('Admin').getAuthInfoRequestById
        if not str(handle):
            raise cherrypy.HTTPRedirect('/%s/list' % (self.classname))
        try:
            result = c2u(func(u2c(handle)))
        except (corba.module.Admin.ObjectNotFound,):
            context['main'] = _("Object_not_found")
            return self._render('base', ctx=context)
        
        context['edit'] = kwd.get('edit')
        context['result'] = result
        return self._render('detail', context)

    @protectedPage
    def resolve(self, **kwd):
        context = {}
        try:
            id_ai = int(kwd.get('id'))
        except (TypeError, ValueError):
            context['main'] = _("Required_integer_as_parameter")
            return self._render('base', ctx=context)
        cherrypy.session.get('Admin').processAuthInfoRequest(id_ai, False)
        raise cherrypy.HTTPRedirect('/%s/list/?reload=1' % (self.classname))

    @protectedPage
    def close(self, **kwd):
        context = {}
        try:
            id_ai = int(kwd.get('id'))
        except (TypeError, ValueError):
            context['main'] = _("Required_integer_as_parameter")
            return self._render('base', ctx=context)
        cherrypy.session.get('Admin').processAuthInfoRequest(id_ai, True)
        raise cherrypy.HTTPRedirect('/%s/list/?reload=1' % (self.classname))


class Invoices(AdifPage, ListTableMixin):

    def __init__(self):
        AdifPage.__init__(self)
        ListTableMixin.__init__(self)

    @protectedPage
    def filter(self, **kwd):
        context = {}
        context['result'] = {}
        context['result']['typelist'] = self._invoiceTypeList()
        return self._render('filter', ctx=context)

    @protectedPage
    def detail(self, **kwd):
        context = {}
        try:
            handle = int(kwd.get('id', None))
        except (TypeError, ValueError):
            context['main'] = _("Required_integer_as_parameter")
            return self._render('base', ctx=context)
        func = cherrypy.session.get('Admin').getInvoiceById
        if not str(handle):
            raise cherrypy.HTTPRedirect('/%s/list/' % (self.classname))
        try:
            result = c2u(func(u2c(handle)))
        except (corba.module.Admin.ObjectNotFound,):
            context = _("Object_not_found")
            return self._render('base', ctx=context)
        context['edit'] = kwd.get('edit')

        # hack hack hack - omniorb python mapping maps structs to class with dict objects inside, 
        # and setting attribute propagates this change, so this works
        filemanager = cherrypy.session.get('FileManager')
        if result.filePDF:
            result.filePDFinfo = filemanager.info(result.filePDF)
        if result.fileXML:
            result.fileXMLinfo = filemanager.info(result.fileXML)
        # hack, these need remapping to other values.
        if result.actions:
            [ x.__dict__.__setitem__('actionType', 'RREG') for x in result.actions if x.actionType == 0 ]
            [ x.__dict__.__setitem__('actionType', 'RUDR') for x in result.actions if x.actionType == 1 ]
        result.type = [ x['type'] for x in corba.module.Invoicing.Invoices if x['obj']._n == result.type ][0]
        context['result'] = result
        return self._render('detail', context)

    @protectedPage
    def attachment(self, **kwd):
        context = {}
        try:
            handle = int(kwd.get('id', None))
        except (TypeError, ValueError):
            context['main'] = _("Required_integer_as_parameter")
            return self._render('base', ctx=context)
        if handle:
            response = cherrypy.response
            filemanager = cherrypy.session.get('FileManager')
            info = filemanager.info(handle)
            response.headers['Content-Type'] = info.mimetype
            cd = "%s; filename=%s" % ('attachment', info.name)
            response.headers["Content-Disposition"] = cd
            response.headers['Content-Length'] = info.size
            f = filemanager.load(u2c(handle))
            body = ""
            while 1:
                part = f.download(102400) # 100kBytes
                if part:
                    body = "%s%s" % (body, part)
                else:
                    break
            response.body = body
            return response.body


class Bankstatements(AdifPage, ListTableMixin):

    def __init__(self):
        AdifPage.__init__(self)
        ListTableMixin.__init__(self)

class Development(object):

    __metaclass__ = exposed.exposed

    def __init__(self):
        object.__init__(self)

    def default(self, *params, **kwd):
        return "Devel version<br />%s<br />%s" % (str(params), str(kwd))

    def index(self, *params, **kwd):
        print '---'
        print dir(cherrypy.request)
        print '---'
        
        dvals = [
            "request.remote:'%s'" % cherrypy.request.remote,
            "request.path_info: '%s'" % cherrypy.request.path_info,
            "request.base: '%s'" % cherrypy.request.base,
            "request.query_string: '%s'" % cherrypy.request.query_string,
            "request.request_line: '%s'" % cherrypy.request.request_line,
            #"request.object_path: '%s'" % cherrypy.request.object_path,
            "request.params: '%s'" % cherrypy.request.params,
            "request.wsgi_environ: '%s'" % cherrypy.request.wsgi_environ,
            "params: %s" % str(params),
            "kwd: %s" % str(kwd),
            "config: '%s'" % cherrypy.config,
            #"request.headers['Cherry-Location]: '%s'" % cherrypy.request.headers.get(cfg.get('html', 'header'), '/'),
            "session: '%s'" % cherrypy.session
        ]
        
        output = ''
        for dval in dvals:
            output += "<p>%s\n</p>" % dval
        count = cherrypy.session.get('count', 0) + 1
        cherrypy.session['count'] = count
        return output

class Smaz(Page):
    def index(self):
        context = DictLookup({'main': p("hoj")})
        
        return BaseSiteMenu(context).render()

def runserver():
    print "-----====### STARTING ADIF ###====-----"
    root = ADIF()
    root.summary = Summary()
    root.logs = Logs()
    root.registrars = Registrars()
    root.requests = Requests()
    root.domains = Domains()
    root.contacts = Contacts()
    root.nssets = NSSets()
    root.mails = Mails()
    root.authinfos = AuthInfos()
    root.invoices = Invoices()
    root.bankstatements = Bankstatements()
    root.statistics = Statistics()
    root.devel = Development()
    
    cherrypy.quickstart(root, '/', config=config.cherrycfg)
    

if __name__ == '__main__':
#    from menunode import menu_tree
#    print menu_tree.mprint()
#    from webwidgets.menu import Menu
#    print unicode(Menu(menu_tree, 'sdomains'))
    runserver()