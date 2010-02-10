# !/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from fred_webadmin import setuplog
setuplog.setup_log()


import time
import pprint
import traceback
import types

from logging import debug, error

from cgi import escape

import omniORB
from omniORB import CORBA
from omniORB.any import from_any

# DNS lib imports
import dns.message
import dns.resolver
import dns.query

from fred_webadmin import config
 
if config.auth_method == 'LDAP':
    import ldap

# CherryPy main import
import cherrypy
from cherrypy.lib import http
import simplejson

import fred_webadmin.webwidgets.forms.utils as form_utils
import fred_webadmin.corbarecoder as recoder
import fred_webadmin.utils as utils

from fred_webadmin.logger.sessionlogger import SessionLogger
from fred_webadmin.logger.dummylogger import DummyLogger
from fred_webadmin.logger.codes import logcodes

from fred_webadmin.controller.listtable import ListTableMixin

# decorator for exposing methods
from fred_webadmin import exposed

# CORBA objects
from fred_webadmin.corba import Corba, CorbaServerDisconnectedException
corba = Corba()

from fred_webadmin.corba import ccReg, Registry
from fred_webadmin.translation import _


from fred_webadmin.webwidgets.templates.pages import (
    BaseSite, BaseSiteMenu, LoginPage, DisconnectedPage, NotFound404Page, 
    AllFiltersPage, FilterPage, ErrorPage, DigPage, SetInZoneStatusPage, 
    DomainDetail, ContactDetail, NSSetDetail, KeySetDetail, RegistrarDetail, 
    ActionDetail, PublicRequestDetail, MailDetail, InvoiceDetail, LoggerDetail,
    RegistrarEdit, BankStatementPairingEdit, BankStatementDetail, 
    BankStatementDetailWithPaymentPairing
)
from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget
from fred_webadmin.webwidgets.gpyweb.gpyweb import DictLookup, noesc, attr, ul, li, a, div, span, p, br, pre
from fred_webadmin.webwidgets.utils import isiterable, convert_linear_filter_to_form_output
from fred_webadmin.webwidgets.menu import MenuHoriz
from fred_webadmin.webwidgets.adifwidgets import FilterList, FilterListUnpacked, FilterListCustomUnpacked, FilterPanel
from fred_webadmin.menunode import menu_tree
from fred_webadmin.webwidgets.forms.adifforms import LoginForm
from fred_webadmin.webwidgets.forms.editforms import RegistrarEditForm, BankStatementPairingEditForm
from fred_webadmin.webwidgets.forms.filterforms import *
from fred_webadmin.webwidgets.forms.filterforms import get_filter_forms_javascript

from fred_webadmin.itertable import IterTable, fileGenerator, CorbaFilterIterator
from fred_webadmin.utils import json_response, get_current_url

from fred_webadmin.mappings import (f_name_enum, 
                      f_name_id, 
                      f_name_get_by_handle, 
                      f_name_filterformname,
                      f_name_editformname, 
                      f_urls, 
                      f_name_actionfiltername, 
                      f_name_actiondetailname)
from fred_webadmin.user import User

from fred_webadmin.customview import CustomView

from fred_webadmin.controller.perms import check_onperm, check_nperm, login_required


class AdifError(Exception):
    pass
class PermissionDeniedError(AdifError):
    pass
class IorNotFoundError(AdifError):
    pass

class LDAPBackend:
    def __init__(self):
        self.ldap_scope = config.LDAP_scope
        self.ldap_server = config.LDAP_server
        
    def authenticate(self, username=None, password=None):
        l = ldap.open(config.LDAP_server)
        l.simple_bind_s(self.ldap_scope % username, password)


class Page(object):
    """ Index page, similiar to index.php, index.html and so on.
    """
    __metaclass__ = exposed.AdifPageMetaClass

    def default(self, *params, **kwd):
        """catch-all for any non-defined method"""
        return '%s,%s,%s' % (self.__class__, params, kwd)


class AdifPage(Page):
    def __init__(self):
        Page.__init__(self)
        self.classname = self.__class__.__name__.lower()
        self.menu_tree = menu_tree
    
    def _template(self, action = ''):
        if action == 'base':
            return BaseSiteMenu
        if action == 'login':
            return LoginPage
        elif action in ('filter', 'list'):
            return FilterPage
        elif action == 'allfilters':
            return AllFiltersPage
        elif action == 'disconnected':
            return DisconnectedPage
        elif action == '404_not_found':
            cherrypy.response.status = 404
            return NotFound404Page
        elif action == 'error':
            return ErrorPage
        elif action == 'dig':
            return DigPage
        elif action == 'pairstatements':
            return BankStatementPairingEdit
        elif action == 'setinzonestatus':
            return SetInZoneStatusPage
        else:
            # returns ClassName + Action (e.g. DomainDetail) class from module of this class, if there is no such, then it returns BaseSiteMenu: 
            template_name = self.__class__.__name__ + action.capitalize()
            debug('Snazim se vzit templatu jmenem:' + template_name)
            template = getattr(sys.modules[self.__module__], template_name, None)
            if template is None:
                error("TEMPLATE %s IN MODULE %s NOT FOUND, USING DEFAULT: BaseSiteMenu" % (template_name, sys.modules[self.__module__]))
                template = BaseSiteMenu 
            else:
                debug('...OK, template %s taken' % template_name)
            if not issubclass(template, WebWidget):
                raise RuntimeError('%s is not derived from WebWidget - it cannot be template!' % repr(template))
            return template
        
    def _get_menu(self, action):
        return MenuHoriz(self.menu_tree, self._get_menu_handle(action), cherrypy.session['user'])
    
    def _get_menu_handle(self, action):
        if self.classname in ('registrar'):
            if action in ('allfilters', 'filter'):
                return self.classname + 'filter'
            elif action in ('create', 'list'): 
                return self.classname + action
        if self.classname == 'file':
            return 'summary'
            
        return self.classname

    def _get_selected_menu_body_id(self, action):
        handle = self._get_menu_handle(action)
        menu_node = self.menu_tree.get_menu_by_handle(handle)
        if menu_node is None:
            return ''
            #raise MenuDoesNotExistsError(handle)
        return menu_node.body_id
    
    def _render(self, action='', ctx=None):
        context = DictLookup()
        context.approot = '/'
        context.classname = self.classname
        context.classroot = "%s%s/" % (context.approot, context.classname)
        context.corba_server = cherrypy.session.get('corba_server_name')
        context.request = cherrypy.request
        context.history = cherrypy.session.get('history', False)

        user = cherrypy.session.get('user', None)
        if user: 
            context.user = user 
            context.menu = self._get_menu(action) or None # Login page has no menu
            context.body_id = self._get_selected_menu_body_id(action)
        
        if ctx:
            context.update(ctx)
        
        temp_class = self._template(action)(context)
        result = temp_class.render()
        
        return result

    def default(self, *params, **kwd):
        #raise cherrypy.HTTPRedirect('/%s' % (self.classname))
        if config.debug:
            return '%s<br/>%s' % (str(kwd), str(params))
        else:
            return self._render('404_not_found')

    def remove_session_data(self):
        cherrypy.session['user'] = None
        cherrypy.session['corbaSession'] = None
        cherrypy.session['corbaSessionString'] = None
        cherrypy.session['corba_server_name'] = None
        cherrypy.session['Admin'] = None
        cherrypy.session['Mailer'] = None
        cherrypy.session['FileManager'] = None
        cherrypy.session['filter_forms_javascript'] = None
        

class ADIF(AdifPage):
    def _get_menu_handle(self, action):
        return 'summary'
    
    @login_required
    def index(self, *args):
        if cherrypy.session.get('user'):
            raise cherrypy.HTTPRedirect('/summary/')
        else:
            raise cherrypy.HTTPRedirect('/login/')

    def default(self, *args, **kwd):
        if args:
            if args[0] == 'filter_forms_javascript.js':
                if config.caching_filter_form_javascript:
                    if cherrypy.session.get('filter_forms_javascript') is not None:
                        since = cherrypy.request.headers.get('If-Unmodified-Since') 
                        since2 = cherrypy.request.headers.get('If-Modified-Since')
                        if since or since2:
                            raise cherrypy.HTTPRedirect("", 304)
                    cherrypy.response.headers['Last-Modified'] = http.HTTPDate(time.time())
                
                result = get_filter_forms_javascript()
                cherrypy.session['filter_forms_javascript'] = result 
                return result
            elif args[0] == 'set_history':
                new_history = simplejson.loads(kwd.get('history', 'false'))
                cherrypy.session['history'] = new_history
                utils.get_corba_session().setHistory(new_history)
                debug('History set to %s' % new_history)
                return json_response(new_history)
        return super(ADIF, self).default(*args, **kwd)
        
        
    def login(self, *args, **kwd):
        if cherrypy.session.get('corbaSessionString'): # already logged in
            debug('Already logged in, corbaSessionString = %s' % 
                   cherrypy.session.get('corbaSessionString'))
            log_req = cherrypy.session['Logger'].create_request(
                cherrypy.request.remote.ip, 
                cherrypy.request.body, "Login")
            log_req.update("warning", logcodes["AlreadyLoggedIn"])
            log_req.commit()

            raise cherrypy.HTTPRedirect('/summary/')
        if kwd:
            if cherrypy.request.method == 'GET' and kwd.get('next'):
                form = LoginForm(action='/login/', method='post')
                form.fields['next'].value = kwd['next']
            else:
                form = LoginForm(kwd, action='/login/', method='post')
        else:
            form = LoginForm(action='/login/', method='post')
        
        if form.is_valid():
            debug('form is valid')
            login = form.cleaned_data.get('login', '')
            password = form.cleaned_data.get('password', '')

            corba_server = int(form.cleaned_data.get('corba_server', 0))
            try:
                ior = config.iors[corba_server][1]
                nscontext = config.iors[corba_server][2]
                corba.connect(ior, nscontext)
                admin = corba.getObject('Admin', 'Admin')

                if not config.session_logging_enabled:
                    # DummyLogger provides correct interface, but does
                    # not log anything
                    logger = DummyLogger()
                else:
                    # Add corba logger to the cherrypy session object, so that
                    # it can be found by CorbaLazyRequest.
                    corba_logd = corba.getObject("Logger", "Logger")
                    cherrypy.session['corba_logd'] = corba_logd
                    logger = SessionLogger(dao=corba_logd)
                    
                logger.start_session("en", login)
                cherrypy.session['Logger'] = logger
                log_req = logger.create_request(cherrypy.request.remote.ip, 
                                                cherrypy.request.body, 
                                                "Login")
                log_req.update("username", login)
                
                if config.auth_method == 'LDAP':
                    # Throws ldap.INVALID_CREDENTIALS if user is not valid.
                    LDAPBackend().authenticate(login, password) 
                else:
                    admin.authenticateUser(recoder.u2c(login), recoder.u2c(password)) 
                
                corbaSessionString = admin.createSession(recoder.u2c(login))

                logger.set_common_property("session_id", corbaSessionString)

                # I have to log session_id now because this logging request has
                # been created before setting the session_id as a common
                # property.
                log_req.update("session_id", corbaSessionString)

                cherrypy.session['corbaSessionString'] = corbaSessionString
                
                cherrypy.session['corba_server_name'] = \
                    form.fields['corba_server'].choices[corba_server][1]
                cherrypy.session['Admin'] = admin
                cherrypy.session['filter_forms_javascript'] = None
                
                cherrypy.session['user'] = User(utils.get_corba_session().getUser())
                
                cherrypy.session['Mailer'] = corba.getObject('Mailer', 'Mailer')
                cherrypy.session['FileManager'] = corba.getObject('FileManager',
                                                                  'FileManager')
                
                cherrypy.session['history'] = False
                utils.get_corba_session().setHistory(False)

                redir_addr = form.cleaned_data.get('next')
                
                log_req.commit("") 

                raise cherrypy.HTTPRedirect(redir_addr)
            
            except omniORB.CORBA.BAD_PARAM, e:
                log_req.update("result", str(e))
                log_req.commit("") 
                form.non_field_errors().append(_('Bad corba call! ') + '(%s)' %
                                                (str(e)))
                if config.debug:
                    form.non_field_errors().append(noesc(escape(unicode(
                        traceback.format_exc())).replace('\n', '<br/>')))
            except ccReg.Admin.AuthFailed, e:
                log_req.update("result", str(e))
                log_req.commit("") 
                form.non_field_errors().append(_('Login error, please enter '
                                                 'correct login and password'))
                log_req.update("error", logcodes["AuthFailed"])
                if config.debug:
                    form.non_field_errors().append('(type: %s, exception: %s)' %
                                                   (escape(unicode(type(e))), 
                                                   unicode(e)))
                    form.non_field_errors().append(noesc(escape(unicode(
                        traceback.format_exc())).replace('\n', '<br/>')))
            except Exception, e:
                # log_req.update("result", str(e))
                # log_req.commit("") 
                if config.auth_method == 'LDAP':
                    if isinstance(e, ldap.INVALID_CREDENTIALS):
                        form.non_field_errors().append(_('Invalid username '
                                                         'and/or password!'))
                        log_req.update("warning", logcodes["InvalidLogin"])
                        log_req.commit();
                        if config.debug:
                            form.non_field_errors().append('(%s)' % str(e))
                    elif isinstance(e, ldap.SERVER_DOWN):
                        form.non_field_errors().append(_('LDAP server is '
                                                         'unavailable!'))
                    else:
                        raise
                else:
                    raise

        form.action = '/login/'
        return self._render('login', {'form': form})
      
    @login_required
    def logout(self):
        if cherrypy.session.get('Admin'):
            try:
                cherrypy.session['Admin'].destroySession(
                    recoder.u2c(cherrypy.session['corbaSessionString']))
            except CORBA.TRANSIENT, e:
                debug('Admin.destroySession call failed, backend server '
                      'is not running.\n%s' % e)

        if cherrypy.session.get('Logger'):
            req = cherrypy.session['Logger'].create_request(
                cherrypy.request.remote.ip, cherrypy.request.body, "Logout")
            req.commit("") 
            cherrypy.session['Logger'].close_session()
        
        self.remove_session_data()
        
        raise cherrypy.HTTPRedirect('/')


class Summary(AdifPage):

    def _template(self, action=''):
        if action == 'summary':
            return BaseSiteMenu
        else:
            return super(Summary, self)._template(action)
        
    @login_required
    def index(self):
        context = DictLookup()
        context.main = ul(li(a(attr(href='''/file/filter/?json_data=[{%22presention|CreateTime%22:%22on%22,%22CreateTime/3%22:%2210%22,%22CreateTime/0/0%22:%22%22,%22CreateTime/0/1/0%22:%220%22,%22CreateTime/0/1/1%22:%220%22,%22CreateTime/1/0%22:%22%22,%22CreateTime/1/1/0%22:%220%22,%22CreateTime/1/1/1%22:%220%22,%22CreateTime/4%22:%22-2%22,%22CreateTime/2%22:%22%22,%22presention|Type%22:%22000%22,%22Type%22:%225%22}]'''), _('Domain expiration letters'))))
        return self._render('summary', ctx=context)
    
    
class Logger(AdifPage, ListTableMixin):
    """ If cherrypy.session.get("corba_logd") is not None, then we know that
        corba logger is present, so we should be able to display the logged
        events.
        Otherwise just print a warning (that's kind of the best we can do).
    """

    def filter(self, *args, **kwd):
        if config.session_logging_enabled:
            return ListTableMixin.filter(self, *args, **kwd)
        else:
            return self.index()

    def allfilters(self, *args, **kwd):
        if config.session_logging_enabled:
            return ListTableMixin.allfilters(self, *args, **kwd)
        else:
            return self.index()

    def detail(self, **kwd):
        if config.session_logging_enabled:
            return ListTableMixin.detail(self, **kwd)
        else:
            return self.index()

    def index(self):
        if config.session_logging_enabled:
            return ListTableMixin.index(self)
        else:
            context = DictLookup()
            context.main = p(
                "Session logging disabled (see your webadmin_cfg.py).")
            return self._render('base', ctx=context)


class Statistics(AdifPage):
    def _template(self, action=''):
        return BaseSiteMenu


class Registrar(AdifPage, ListTableMixin):
    def __init__(self):
        AdifPage.__init__(self)
        ListTableMixin.__init__(self)
        # Some fields must be treated specially (their value must be converted
        # to a corba type first). We use self.type_transformer to map the names
        # of these fields to their respective converting functions.
        # All the other fields (i.e., those not in the transformer mapping) 
        # are treated as strings.
        self.type_transformer = {}
        self.type_transformer['zones'] = lambda val: map(
            lambda x: ccReg.ZoneAccess(**x), val)
        self.type_transformer['access'] = lambda val: map(
            lambda x: ccReg.EPPAccess(**x), val)
        self.type_transformer['id'] = lambda val: int(val)

    def _get_empty_corba_struct(self):
        """ Creates a ccReg.Registrar object representing
            a new registrar to be created on server side. """
        new = []
        new.append(0) # id
        new.extend(['']*3)
        new.append(False) # vat
        new.extend(['']*9)
        admin = cherrypy.session.get('Admin') 
        new.extend([admin.getDefaultCountry()])
        new.extend(['']*4)
        new.append('') # money
        new.append([]) # accesses
        new.append([]) # active zones
        new.append(False) # hidden
        return ccReg.Registrar(*new) # empty registrar

    def _fill_registrar_struct_from_form(self, registrar, cleaned_data, 
      log_request):
        for field_key, field_val in cleaned_data.items():
            # Create the corba object for the respective field.
            if field_key in self.type_transformer:
                corba_val = self.type_transformer[field_key](field_val)
            else:
                corba_val = field_val
            setattr(registrar, field_key, corba_val)
            # Add this action to the audit log.
            log_request.update("set_%s" % field_key, field_val)

    def _process_valid_form(self, form, registrar, reg_id, 
                            context, log_request):
        self._fill_registrar_struct_from_form(
            registrar, form.cleaned_data, log_request)
        corba_reg = recoder.u2c(registrar)
        try:
            reg_id = utils.get_corba_session().updateRegistrar(corba_reg)
        except ccReg.Admin.UpdateFailed, e:
            form.non_field_errors().append(
                "Updating registrar failed. Perhaps you tried to "
                "create a registrar with an already used handle?")
            context['form'] = form
            log_request.update("result", str(e))
            log_request.commit("")
            return self._render('edit', context)
        log_request.commit("")
        try:
            id = int(reg_id)
        except (ValueError, TypeError), e:
            # Paranoid. Note that this should never be caught, because id is 
            # set automatically, not by the user. So it should always have
            # a correct type.
            log_request.update("result", str(e))
            log_request.commit("")
            raise 
        # Jump to the registrar's detail.
        raise cherrypy.HTTPRedirect("/registrar/detail/?id=%s" % reg_id)

    def _update_registrar(self, registrar, log_request_name, *params,**kwd):
        """ Handles the actual updating/creating of a registrar.
            Note that registrar create only differs from registrar update in
            that it create has id == 0.

            Args:
                registrar:
                    The ccReg.Registrar object that is being updated or
                    created.
                log_request:
                    The SessionLogger.LogRequest object that keeps log of
                    this event.
        """
        log_request = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body, 
            log_request_name)
        context = {'main': div()}
        form_class = self._get_editform_class()
        initial = registrar.__dict__

        if cherrypy.request.method == 'POST':
            form = form_class(kwd, initial=initial, method='post')
            if form.is_valid():
                self._process_valid_form(
                    form, registrar, kwd.get('id'), context, log_request)
            else:
                if config.debug:
                    context['main'].add('Form is not valid! Errors: %s' % 
                                         repr(form.errors))
        else:
            form = form_class(method='post', initial=initial) 
        
        context['form'] = form
        return self._render('edit', context)
    
    @check_onperm('write')
    def edit(self, *params, **kwd):
        registrar = self._get_detail(obj_id=kwd.get('id'))
        result = self._update_registrar(registrar, "RegistrarUpdate", *params, **kwd)
        return result

    @check_onperm('write')
    def create(self, *params, **kwd):
        registrar = self._get_empty_corba_struct()
        result = self._update_registrar(registrar, "RegistrarCreate", *params, **kwd)
        return result


class Action(AdifPage, ListTableMixin):
    def _get_menu_handle(self, action):
        if action == 'detail':
            return 'logs'
        else:
            return super(Action, self)._get_menu_handle(action)
    

class Domain(AdifPage, ListTableMixin):
    @check_onperm('read')
    def dig(self, **kwd):
        context = {}
        log_request = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body, 
            "DomainDig")
        handle = kwd.get('handle', None)
        log_request.update("handle", handle)
        if not handle:
            log_request.update("result", "no handle")
            log_request.commit("")
            raise cherrypy.HTTPRedirect(f_urls[self.classname])
        try:
            query = dns.message.make_query(handle, 'ANY')
            resolver = dns.resolver.get_default_resolver().nameservers[0]
            dig = dns.query.udp(query, resolver).to_text()
        except e:
            #TODO(tomas): Log an error?
            log_request.update("result", str(e))
            context['main'] = _("Object_not_found")
            return self._render('base', ctx=context)
        finally:
            log_request.commit("");
        context['handle'] = handle
        context['dig'] = dig
        return self._render('dig', context)

    @check_onperm('write')
    def setinzonestatus(self, **kwd):
        "Call setInzoneStatus(domainID) "
        context = {'error': None}
        domain_id = kwd.get('id', None) # domain ID
        if not domain_id:
            raise cherrypy.HTTPRedirect(f_urls[self.classname])
        
        admin = cherrypy.session.get('Admin')
        if hasattr(admin, "setInZoneStatus"):
            try:
                context['success'] = admin.setInZoneStatus(int(domain_id))
            # TODO(tom): Do not catch generic exception here!
            except Exception, e:
                context['error'] = e
        else:
            context['error'] = _("Function setInZoneStatus() is not implemented in Admin.")
        
        # if it was succefful, redirect into domain detail
        if context['error'] is None:
            # use this URL in trunk version:
            # HTTPRedirect(f_urls[self.classname] + '/detail/?id=%s' % domain_id)
            # this URL is compatible with branche 3.1
            raise cherrypy.HTTPRedirect('/domain/detail/?id=%s' % domain_id)
        
        # display domain name
        try:
            context['handle'] = admin.getDomainById(int(domain_id)).fqdn
        except Exception, e:
            context['error'] = e
        # display page with error message
        return self._render('setinzonestatus', context)



class Contact(AdifPage, ListTableMixin):
    pass
#    def __init__(self):
#        AdifPage.__init__(self)
#        ListTableMixin.__init__(self)

class NSSet(AdifPage, ListTableMixin):
    pass
    
class KeySet(AdifPage, ListTableMixin):
    pass

class Mail(AdifPage, ListTableMixin):
    pass
        
class File(AdifPage, ListTableMixin):
    @check_onperm('read')
    def detail(self, **kwd):
        log_request = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body, 
            "FileDetail")
        context = {}
        try:
            handle = int(kwd.get('id', None))
        except (TypeError, ValueError), e:
            log_request.update("result", str(e))
            log_request.commit()
            context['main'] = _("Required_integer_as_parameter")
            return self._render('base', ctx=context)
        if handle:
            response = cherrypy.response
            filemanager = cherrypy.session.get('FileManager')
            info = filemanager.info(recoder.u2c(handle))
            try:
                f = filemanager.load(recoder.u2c(handle))
                body = ""
                while 1:
                    part = f.download(102400) # 100kBytes
                    if part:
                        body = "%s%s" % (body, part)
                    else:
                        break
                response.body = body
                response.headers['Content-Type'] = info.mimetype
                cd = "%s; filename=%s" % ('attachment', info.name)
                response.headers["Content-Disposition"] = cd
                response.headers['Content-Length'] = info.size
            except ccReg.FileManager.FileNotFound, e:
                log_request.update("result", str(e))
                log_request.commit()
                context['main'] = _("Object_not_found")
                return self._render('file', ctx=context)
            log_request.commit()
            return response.body
        
class PublicRequest(AdifPage, ListTableMixin):
    @check_onperm('write')
    def resolve(self, **kwd):
        '''Accept and send'''
        context = {}
        log_req = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body,
            "PublicRequestAccept")
        try:
            id_pr = int(kwd.get('id'))
            log_req.update("publicrequest_id", id_pr)
            log_req.commit()

        except (TypeError, ValueError):
            log_request.update("result", str(e))
            log_request.commit()
            context['main'] = _("Required_integer_as_parameter")
            return self._render('base', ctx=context)
        try:
            cherrypy.session.get('Admin').processPublicRequest(id_pr, False)
        except ccReg.Admin.REQUEST_BLOCKED, e:
            log_request.update("result", str(e))
            log_request.commit()
            raise CustomView(self._render('error', {'message':
                                                        [_(u'This object is blocked, request cannot be accepted. You can return back to '), 
                                                         a(attr(href=f_urls[self.classname] + 'detail/?id=%s' % id_pr), _('public request.'))
                                                        ]
                                                   }))
            
        raise cherrypy.HTTPRedirect(f_urls[self.classname] + 'filter/?reload=1&load=1')

    @check_onperm('write')
    def close(self, **kwd):
        '''Close and invalidate'''
        context = {}
        req = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body,
            "PublicRequestInvalidate")
        try:
            id_ai = int(kwd.get('id'))
            req.update("publicrequest_id", id_ai)
            req.commit()
        except (TypeError, ValueError), e:
            log_request.update("result", str(e))
            log_request.commit()
            context['main'] = _("Required_integer_as_parameter")
            return self._render('base', ctx=context)
        cherrypy.session.get('Admin').processPublicRequest(id_ai, True)
        raise cherrypy.HTTPRedirect(f_urls[self.classname] + 'filter/?reload=1&load=1' % (self.classname))


class Invoice(AdifPage, ListTableMixin):
    pass


class BankStatement(AdifPage, ListTableMixin):
    def _pair_payment_with_registrar(self, context, payment_id, registrar_handle):
        """ Links the payment with registrar. """
        log_req = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body, "PaymentPair")
        log_req.update("payment_id", payment_id)
        log_req.update("registrar_handle", registrar_handle)
        invoicing = utils.get_corba_session().getBankingInvoicing()
        success = invoicing.pairPaymentRegistrarHandle(
            payment_id, recoder.u2c(registrar_handle))
        if not success:
            log_req.update("result", "Could not pair payment")
        log_req.commit()
        return success

    @check_onperm('read')
    def detail(self, **kwd):
        context = {}
        # Indicator whether the pairing action has been carried out
        # successfully.
        pairing_success = False
        
        log_req = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body, 
            f_name_actiondetailname[self.__class__.__name__.lower()])
        
        registrar_handle = kwd.get('handle')
        obj_id = kwd.get('id')
        try:
            obj_id = int(obj_id)
        except (TypeError, ValueError), e:
            log_request.update("result", str(e))
            log_request.commit()
            context['main'] = _(
                "Requires integer as parameter (got %s)." % obj_id)
            raise CustomView(self._render('base', ctx=context))
        
        # When the user sends the pairing form we arrive at BankStatement
        # detail again, but this time we receive registrar_handle in kwd
        # => pair the payment with the registrar.
        if registrar_handle is not None and obj_id is not None:
            pairing_success = self._pair_payment_with_registrar(
                context, obj_id, registrar_handle)

        detail = utils.get_detail(self.classname, obj_id)

        log_req.update('object_id', kwd.get('id'))
        
        context['detail'] = detail 
        context['form'] = BankStatementPairingEditForm(
            method="POST",
            initial={
                'handle': kwd.get('handle', None),
                'statementId': kwd.get('statementId', None),
                'id': obj_id},
            onsubmit='return confirmAction();')
        if registrar_handle is not None and not pairing_success:
            # Pairing form was submitted, but pairing did not finish
            # successfully => Show an error.
            context['form'].non_field_errors().append(
                """Could not pair. Perhaps you have entered"""
                """ an invalid handle?""")

        log_req.commit("")

        if detail.invoiceId != 0:
            action = 'detail'
        else:
            # Payment not paired => show the payment pairing edit form
            action = 'pair_payment'
            # invoiceId is a link to detail, but for id == 0 this detail does
            # not exist => hide invoiceId value so the link is not "clickable".
            # Note: No information is lost, because id == 0 semantically means 
            # that there is no id.
            context['detail'].invoiceId = ""
        res = self._render(action, context)
        return res

    def _template(self, action = ''):
        if action == "pair_payment":
            # Show detail with payment pairing form.
            template_name = 'BankStatementDetailWithPaymentPairing'
        else:
            # Show normal detail.
            return super(BankStatement, self)._template(action)
        template = getattr(sys.modules[self.__module__], template_name, None)
        if template is None:
            error("TEMPLATE %s IN MODULE %s NOT FOUND, USING DEFAULT: BaseSiteMenu" % (template_name, sys.modules[self.__module__]))
            template = BaseSiteMenu 
        if not issubclass(template, WebWidget):
            raise RuntimeError('%s is not derived from WebWidget - it cannot be template!' % repr(template))
        return template


class Filter(AdifPage, ListTableMixin):
    def _get_menu_handle(self, action):
        return 'summary'
        if action in ('detail', 'filter'):
            return 'summary'
        else:
            return super(Filter, self)._get_menu_handle(action)

   
class Development(object):

    __metaclass__ = exposed.AdifPageMetaClass

    def __init__(self):
        object.__init__(self)

    def default(self, *params, **kwd):
        return "Devel version<br />%s<br />%s" % (str(params), str(kwd))

    def index(self, *params, **kwd):
        debug('---')
        debug(dir(cherrypy.request))
        debug('---')
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
    
    def heapy(self):
        try:
            from guppy import hpy
        except ImportError:
            return 'guppy module not found'
        h=hpy()
        heap = h.heap()
        output = _(u'''This page displays memory consumption by python object on server.
            It propably cause server threads to not work properly!!! 
            DO NOT USE THIS PAGE IN PRODUCTION SYSTEM!!!\n\n''')
                        
        output += u'\n'.join(unicode(heap).split('\n')[:2]) + '\n'
        for i in xrange(heap.partition.numrows):
            item = heap[i]
            output += unicode(item).split('\n')[2] + '\n'
        
        cherrypy.response.headers["Content-Type"] = "text/plain"
        return output

class Smaz(Page):
    def index(self):
        context = DictLookup({'main': p("hoj")})
        
        return BaseSiteMenu(context).render()

class Detail41(AdifPage):
    def index(self):
        #return 'muj index'
        result = utils.get_detail('domain', 41)
        from fred_webadmin.webwidgets.details.adifdetails import DomainDetail as NewDomainDetail
        context = DictLookup({'main': NewDomainDetail(result, cherrypy.session.get('history'))})
        return self._render('base', ctx=context)
    def default(self):
        return 'muj default'


def runserver():
    print "-----====### STARTING ADIF ###====-----"

    root = ADIF()
    root.detail41 = Detail41()
    root.summary = Summary()
    root.logger = Logger()
    root.registrar = Registrar()
    root.action = Action()
    root.domain = Domain()
    root.contact = Contact()
    root.nsset = NSSet()
    root.keyset = KeySet()
    root.mail = Mail()
    root.file = File()
    root.publicrequest = PublicRequest()
    root.invoice = Invoice()
    root.bankstatement = BankStatement()
    root.filter = Filter()
    root.statistic = Statistics()
    root.devel = Development()

    cherrypy.quickstart(root, '/', config=config.cherrycfg)

if __name__ == '__main__':
    runserver()
