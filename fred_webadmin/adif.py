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

# DNS lib imports
import dns.message
import dns.resolver
import dns.query

import config
 
if config.auth_method == 'LDAP':
    import ldap

# CherryPy main import
import cherrypy
from cherrypy.lib import http
import simplejson

import webwidgets.forms.utils as form_utils
from logger.sessionlogger import SessionLogger
from logger.dummylogger import DummyLogger
from logger.codes import logcodes

# decorator for exposing methods
import exposed

# CORBA objects
from corba import Corba, CorbaServerDisconnectedException
corba = Corba()

from corba import ccReg, Registry

from utils import u2c, c2u, get_corba_session, get_detail

from translation import _


from webwidgets.templates.pages import (
    BaseSite, BaseSiteMenu, LoginPage, DisconnectedPage, NotFound404Page, 
    AllFiltersPage, FilterPage, ErrorPage, DigPage, SetInZoneStatusPage, 
    DomainDetail, ContactDetail, NSSetDetail, KeySetDetail, RegistrarDetail, 
    ActionDetail, PublicRequestDetail, MailDetail, InvoiceDetail, LoggerDetail,
    #DomainEdit, ContactEdit, NSSetEdit, 
    RegistrarEdit,
    #ActionEdit, PublicRequestEdit, MailEdit, InvoiceEdit
)
from webwidgets.gpyweb.gpyweb import WebWidget
from webwidgets.gpyweb.gpyweb import DictLookup, noesc, attr, ul, li, a, div, span, p, br, pre
from webwidgets.utils import isiterable, convert_linear_filter_to_form_output
from webwidgets.menu import MenuHoriz
from webwidgets.adifwidgets import FilterList, FilterListUnpacked, FilterListCustomUnpacked, FilterPanel
from menunode import menu_tree
import fred_webadmin
from fred_webadmin.webwidgets.forms.adifforms import LoginForm
from fred_webadmin.webwidgets.forms.editforms import RegistrarEditForm
from fred_webadmin.webwidgets.forms.filterforms import *
from fred_webadmin.webwidgets.forms.filterforms import get_filter_forms_javascript

from itertable import IterTable, fileGenerator, CorbaFilterIterator
from fred_webadmin.utils import json_response, get_current_url

from mappings import (f_name_enum, 
                      f_name_id, 
                      f_name_get_by_handle, 
                      f_name_filterformname,
                      f_name_editformname, 
                      f_urls, 
                      f_name_actionfiltername, 
                      f_name_actiondetailname)
from user import User

from customview import CustomView



class AdifError(Exception):
    pass
class PermissionDeniedError(AdifError):
    pass
class IorNotFoundError(AdifError):
    pass

def login_required(view_func):
    ''' decorator for login-required pages '''
    def _wrapper(*args, **kwd):
        if cherrypy.session.get('user', None):
            return view_func(*args, **kwd)
        redir_addr = '/login/?next=%s' % get_current_url(cherrypy.request)
        raise cherrypy.HTTPRedirect(redir_addr)
    #update_wrapper(_wrapper, view_func)
    return _wrapper


def check_nperm(nperms, nperm_type='all'):
    ''' decorator for login-required and negative permissions check '''
    def _decorator(view_func):
        def _wrapper(*args, **kwd):
            user = cherrypy.session.get('user', None)
            if user:
                if not user.check_nperms(nperms, nperm_type):
                    return view_func(*args, **kwd)
                else:
                    context = {'main': div()}
                    context['main'].add(p(_("You don't have permissions for this page!")))
                    if config.debug:
                        context['main'].add(p('nperms=%s, nperm_type=%s' % (nperms, nperm_type)))
                    return BaseSiteMenu(context).render()

            redir_addr = '/login/?next=%s' % get_current_url(cherrypy.request)
            raise cherrypy.HTTPRedirect(redir_addr)
        
        return _wrapper
    #update_wrapper(_wrapper, view_func)
    return _decorator

def check_onperm(objects_nperms, check_type='all'):
    def _decorator(view_func):
        def _wrapper(*args, **kwd):
            self = args[0]
            user = cherrypy.session.get('user', None)
            if user:
                fred_webadmin.utils.details_cache = {} # invalidate details cache
                nperms = []
                if isinstance(objects_nperms, types.StringTypes):
                    onperms = [objects_nperms]
                else:
                    onperms = objects_nperms
                for objects_nperm in onperms:
                    nperms.append('%s.%s' % (objects_nperm, self.classname))
                if user.check_nperms(nperms, check_type):
                    context = {'message': div()}
                    context['message'].add(p(_("You don't have permissions for this page!")))
                    if config.debug:
                        context['message'].add(p('usernperm = %s,' % user.nperms, br(),
                                                 'nperms=%s,' % nperms, br(),
                                                 'nperm_type=%s' % check_type, br()))
                        context['message'].add(p('a tohle to je udelano nejsofistikovanejsim decoratorem'))
                    return self._render('error', context)
                return view_func(*args, **kwd)

            redir_addr = '/login/?next=%s' % get_current_url(cherrypy.request)
            raise cherrypy.HTTPRedirect(redir_addr)
        
        return _wrapper
    #update_wrapper(_wrapper, view_func)
    return _decorator

class LDAPBackend:
    def __init__(self):
        self.ldap_scope = config.LDAP_scope
        self.ldap_server = config.LDAP_server
        
    def authenticate(self, username=None, password=None):
        l = ldap.open(config.LDAP_server)
        l.simple_bind_s(self.ldap_scope % username, password)
        

class ListTableMixin(object):

    __metaclass__ = exposed.AdifPageMetaClass

    def _get_itertable(self, request_object = None):
        if not request_object:
            request_object = self.classname
        key = cherrypy.session.get('corbaSessionString', '')
        size = config.tablesize
        if cherrypy.session.get('user') and cherrypy.session.get('user').table_page_size:
            size = cherrypy.session.get('user').table_page_size
        itertable = IterTable(request_object, key, size)

        return itertable

    def _get_list(self, context, cleaned_filters=None, **kwd):
        table = self._get_itertable()
        show_result = True
        
        try:
            page = int(kwd.get('page', 1))
        except (ValueError, TypeError):
            page = 1
        try:
            sort_col = kwd.get('sort_col')
            if sort_col is not None:
                sort_col = int(kwd.get('sort_col'))
        except (ValueError, TypeError):
            sort_col = 1
        try:
            sort_dir = bool(int(kwd.get('sort_dir', 1)))
        except (ValueError, TypeError):
            sort_dir = True
        
        
        if cleaned_filters is not None:
            table.set_filter(cleaned_filters)
            if kwd.get('save_input'): # save filter
                table.save_filter(kwd['save_input'])
                context['main'].add(_('Filter saved as "%s"') % kwd['save_input'])
                show_result = False
            else: # normal setting filter
                table.reload()
        if kwd.get('filter_id'): # load filter
            table.load_filter(int(kwd.get('filter_id')))
            if kwd.get('show_form') or not table.all_fields_filled():
                show_result = False
                filter_data = table.get_filter_data()
                form_class = self._get_filterform_class()
                context['form'] = UnionFilterForm(filter_data, data_cleaned=True, form_class=form_class)
            else:
                table.reload()

                
        if kwd.get('cf'):
            table.clear_filter()
        if kwd.get('reload'):
            table.reload()
        if kwd.get('load'): # load current filter from backend
            cleaned_filter_data = table.get_filter_data()
            form_class = self._get_filterform_class()
            form = UnionFilterForm(cleaned_filter_data, form_class=form_class, data_cleaned=True)
            context['form'] = form
            context['show_form'] = kwd.get('show_form')
            if config.debug:
                context['main'].add('kwd_json_data_loaded:', cleaned_filter_data)
        if kwd.get('list_all'):
            table.clear_filter()
            table._table.add()
            table.reload()
        if sort_col is not None:
            table.set_sort(sort_col, sort_dir)

        if show_result:
            if table.num_rows == 0:
                context['result'] = _("No_entries_found")
            if table.num_rows == 1:
                rowId = table.get_row_id(0)
                raise cherrypy.HTTPRedirect(f_urls[self.classname] + 'detail/?id=%s' % rowId)
            if kwd.get('txt', None):
                cherrypy.response.headers["Content-Type"] = "text/plain"
                cherrypy.response.headers["Content-Disposition"] = "inline; filename=%s_%s.txt" % (self.classname, time.strftime('%Y-%m-%d'))
                return fileGenerator(table)
            elif kwd.get('csv', None):
                #cherrypy.response.headers["Content-Type"] = "application/vnd.ms-excel"
                cherrypy.response.headers["Content-Type"] = "text/plain"
                cherrypy.response.headers["Content-Disposition"] = "attachement; filename=%s_%s.csv" % (self.classname, time.strftime('%Y-%m-%d'))
                return fileGenerator(table)
            table.set_page(page)
            
            context['itertable'] = table
        return context

   
    @check_onperm('read')
    def _filter_json_header(self):
        itertable = self._get_itertable()
        return json_response({
            'header': itertable.header,
            'header_type': itertable.header_type,
            'page_size': itertable.page_size,
            'object_name': itertable.request_object,
        })
    
    @check_onperm('read')
    def _filter_json_rows(self, **kwd):
        debug("A json rows delam s kwd: %s" % kwd)
        itertable = self._get_itertable()
        if kwd.get('sort') is not None and kwd.get('dir') is not None:
            itertable.set_sort_by_name(kwd['sort'], kwd['dir'])
        
        rows = itertable.get_rows_dict(kwd.get('start'), kwd.get('limit'))

        #rows = itertable.get_rows_dict(kwd.get('start', 0), kwd.get('limit', itertable.page_size))
        
        json_data = json_response({
            'rows': rows,
            'num_rows': itertable.num_rows,
        })
        debug("vracim json_data = %s" % json_data)
        return json_data
    
    @check_onperm('read')
    def filter(self, *args, **kwd):
        debug('filter ARGS:%s' % unicode(args))

        log_req = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body, 
            f_name_actionfiltername[self.__class__.__name__.lower()])

        if args:
            if args[0] == 'jsondata':
                return self._filter_json_rows(**kwd)
            elif args[0] == 'jsonheader':
                return self._filter_json_header()

        if kwd:
            debug('Incomming data: %s' % kwd)
        context = {'main': div()}
        
        action = 'filter'
        if kwd.get('list_all'):
            action = 'list'

        if kwd.get('txt') or kwd.get('csv'):
            return self._get_list(context, **kwd)
        elif kwd.get('cf') or kwd.get('page') or kwd.get('load') or kwd.get('list_all') or \
            kwd.get('filter_id') or kwd.get('sort_col'): # clear filter - whole list of objects without using filter form
            context = self._get_list(context, **kwd)
        else:
            form_class = self._get_filterform_class()
            # bound form with data
            if kwd.get('json_data') or kwd.get('json_linear_filter'):
                if kwd.get('json_linear_filter'):
                    kwd['json_data'] = simplejson.dumps(convert_linear_filter_to_form_output(simplejson.loads(kwd['json_linear_filter'])))
                debug('Form inicializuju datama' % kwd)
                form = UnionFilterForm(kwd, form_class=form_class)
            else:
                form = UnionFilterForm(form_class=form_class)
            context['form'] = form
            if form.is_bound and config.debug:
                context['main'].add(p(u'kwd:' + unicode(kwd)))
            if form.is_valid():
                if config.debug:
                    context['main'].add(p(u'Jsem validni'))
                    context['main'].add(u'cleaned_data:' + unicode(form.cleaned_data), br())
                debug(u'cleaned_data:' + unicode(form.cleaned_data))
                context = self._get_list(context, form.cleaned_data, **kwd)

                context['main'].add(u"rows: " + str(self._get_itertable().num_rows))
                log_req.update("result_size", self._get_itertable().num_rows)
                # Log the selected filters.
                # TODO(tomas): Log OR operators better...
                for name, value, neg in form_utils.flatten_form_data(
                    form.cleaned_data):
                    log_req.update("filter_%s" % name, value)
                    log_req.update("negation", str(neg), child=True)

                log_req.commit("")

                return self._render('filter', context)
            else:
                
                if form.is_bound and config.debug:
                    context['main'].add(u'Jsem nevalidni, errors:' + unicode(form.errors.items()))
                context['headline'] = '%s filter' % self.__class__.__name__
        
        return self._render(action, context)

    @check_onperm('read')
    def allfilters(self, *args, **kwd):
        context = {'main': div()}
        
        itertable = self._get_itertable('filter')
        #itertable.set_filter({})
        itertable.set_filter([{#'userId': cherrypy.session.get('user').id,
                              'Type': [False, f_name_id[self.classname]]
                             }])
        itertable.reload()
        context['filters_list'] = FilterListCustomUnpacked(itertable.get_rows_dict(raw_header=True), self.classname)
        return self._render('allfilters', context)

    @check_onperm('read')
    def detail(self, **kwd):
        req = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body, 
            f_name_actiondetailname[self.__class__.__name__.lower()])

        context = {}
        
        result = self._get_detail(obj_id=kwd.get('id'))

        req.update("object_id", kwd.get("id"))
        
        context['edit'] = kwd.get('edit', False)
        context['result'] = result
        req.commit("")
        return self._render('detail', context)

    def _get_editform_class(self):
        form_name = f_name_editformname[self.classname]
        form_class = getattr(sys.modules[self.__module__], form_name, None)
        if not form_class:
            raise RuntimeError('No such formclass in modules "%s"' % form_name)
        return form_class
    
    def _get_filterform_class(self):
        form_name = f_name_filterformname[self.classname]
        form_class = getattr(sys.modules[self.__module__], form_name, None)
        if not form_class:
            raise RuntimeError('No such formclass in modules "%s"' % form_name)
        return form_class
    
    @login_required
    def index(self):
        if (config.debug or f_urls.has_key(self.classname)):
            raise cherrypy.HTTPRedirect(f_urls[self.classname] + 'allfilters/')
        else:
            # In production (non-debug) environment we just fall back to 
            # /summary.
            raise NotImplementedError("Support for '%s' has not yet been "
                                      "implemented." % self.classname)

    @check_onperm('read')
    def _get_detail(self, obj_id):
        context = {}
        try:
            obj_id = int(obj_id)
        except (TypeError, ValueError):
            context['main'] = _("Required_integer_as_parameter")
            raise CustomView(self._render('base', ctx=context))

        try:
            return get_detail(self.classname, obj_id)
        except (ccReg.Admin.ObjectNotFound,):
            context['main'] = _("Object_not_found")
            raise CustomView(self._render('base', ctx=context))


class Page(object):

    __metaclass__ = exposed.AdifPageMetaClass

#    def index(self):
#        """index page, similiar to index.php, index.html and so on"""

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
        debug(u"TAKING TEMPLATE:%s" % repr(temp_class))
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
                get_corba_session().setHistory(new_history)
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
                    admin.authenticateUser(u2c(login), u2c(password)) 
                
                corbaSessionString = admin.createSession(u2c(login))

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
                
                cherrypy.session['user'] = User(get_corba_session().getUser())
                
                cherrypy.session['Mailer'] = corba.getObject('Mailer', 'Mailer')
                cherrypy.session['FileManager'] = corba.getObject('FileManager',
                                                                  'FileManager')
                
                cherrypy.session['history'] = False
                get_corba_session().setHistory(False)

                redir_addr = form.cleaned_data.get('next')
                
                log_req.commit("") 

                raise cherrypy.HTTPRedirect(redir_addr)
            
            except omniORB.CORBA.BAD_PARAM, e:
                form.non_field_errors().append(_('Bad corba call! ') + '(%s)' %
                                                (str(e)))
                if config.debug:
                    form.non_field_errors().append(noesc(escape(unicode(
                        traceback.format_exc())).replace('\n', '<br/>')))
            except ccReg.Admin.AuthFailed, e:
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
                    u2c(cherrypy.session['corbaSessionString']))
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
#        context.main = ul(
#            li(a(attr(href='/naky_url/'), u'Dopisy')),
#        )
        #context.main = FilterPanel([[_('Mails'), 'file', [{'Type': '5'}]]])
        #context.main = ul(li(a(attr(href='''/file/filter/?json_data=[{\'presention|Type\':\'000\',\'Type\':\'5\'}]'}'''), _('Mails'))))
        #context.main = ul(li(a(attr(href="/file/filter/?json_linear_filter=[{%22Type%22:%225%22}]"), _('Mails'))))
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
#    def __init__(self):
#        AdifPage.__init__(self)
#        ListTableMixin.__init__(self)
    
    def _get_empty_corba_struct(self):
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
        new.append(False) # hidden
        return ccReg.Registrar(*new) # empty registrar


    def _update_registrar(self, registrar, log_request, *params,**kwd):
        kwd['edit'] = True
        context = {'main': div()}
        form_class = self._get_editform_class()
        initial = registrar.__dict__

        if cherrypy.request.method == 'POST':
            form = form_class(kwd, initial=initial, method='post')
            debug("KWD: %s" % kwd)
            context['main'].add(pre(('KWD: %s' % kwd).replace(',', ',\n')))
            if form.is_valid():
                if debug:
                    context['main'].add(pre(unicode('Cleaned_data:\n%s' % 
                                                     form.cleaned_data).replace(
                                                        ',', ',\n')))
                obj = self._get_empty_corba_struct()
                for key, val in form.cleaned_data.items():
                    if key == 'id':
                        val = int(val)
                    if key == 'access':
                        for i in range(len(val)):
                            print "ACC[%s]=%s" % (i, val[i])
                            val[i] = ccReg.EPPAccess(**val[i])
                    setattr(obj, key, val)
                    log_request.update("set_%s" % key, val)
                debug('Saving registrar: %s' % obj)
                try:
                    get_corba_session().updateRegistrar(u2c(obj))
                except:
                    form.non_field_errors().append("Updating registrar failed."
                                                    "Did you try to create a "
                                                    "registrar with an "
                                                    "already used handle?")
                    context['form'] = form
                    return self._render('edit', context)
                log_request.commit("")
                raise cherrypy.HTTPRedirect(get_current_url(cherrypy.request))
            else:
                if debug:
                    context['main'].add('Form is not valid! Errors: %s' % 
                                         repr(form.errors))
        else:
            form = form_class(method='post', initial=initial) 
        
        log_request.commit("")
        context['form'] = form
        return self._render('edit', context)
    
    @check_onperm('write')
    def edit(self, *params, **kwd):
        registrar = self._get_detail(obj_id=kwd.get('id'))
        log_request = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body, 
            "RegistrarUpdate")
        return self._update_registrar(registrar, log_request, *params, **kwd)

    @check_onperm('write')
    def create(self, *params, **kwd):
        log_request = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body, 
            "RegistrarCreate")
        registrar = self._get_empty_corba_struct()
        return self._update_registrar(registrar, log_request, *params, **kwd)


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
            log_request.commit("")
            raise cherrypy.HTTPRedirect(f_urls[self.classname])
        try:
            query = dns.message.make_query(handle, 'ANY')
            resolver = dns.resolver.get_default_resolver().nameservers[0]
            dig = dns.query.udp(query, resolver).to_text()
        except:
            #TODO(tomas): Log an error?
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
            try:
                f = filemanager.load(u2c(handle))
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
                context['main'] = _("Object_not_found")
                return self._render('file', ctx=context)

            return response.body
        
class PublicRequest(AdifPage, ListTableMixin):
    @check_onperm('write')
    def resolve(self, **kwd):
        '''Accept and send'''
        context = {}
        req = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body,
            "PublicRequestAccept")
        try:
            id_pr = int(kwd.get('id'))
            req.update("publicrequest_id", id_pr)
            req.commit()

        except (TypeError, ValueError):
            context['main'] = _("Required_integer_as_parameter")
            return self._render('base', ctx=context)
        try:
            cherrypy.session.get('Admin').processPublicRequest(id_pr, False)
        except ccReg.Admin.REQUEST_BLOCKED:
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
        except (TypeError, ValueError):
            context['main'] = _("Required_integer_as_parameter")
            return self._render('base', ctx=context)
        cherrypy.session.get('Admin').processPublicRequest(id_ai, True)
        raise cherrypy.HTTPRedirect(f_urls[self.classname] + 'filter/?reload=1&load=1' % (self.classname))


class Invoice(AdifPage, ListTableMixin):
    pass

class Bankstatement(AdifPage, ListTableMixin):
    pass

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

#        while suboutput:
#            output += suboutput + u'\n'
#            more = more.more
#            suboutput = unicode(more)
#            print suboutput
            
        
        cherrypy.response.headers["Content-Type"] = "text/plain"
        return output

class Smaz(Page):
    def index(self):
        context = DictLookup({'main': p("hoj")})
        
        return BaseSiteMenu(context).render()

class Detail41(AdifPage):
    def index(self):
        #return 'muj index'
        result = get_detail('domain', 41)
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
    root.bankstatement = Bankstatement()
    root.filter = Filter()
    root.statistic = Statistics()
    root.devel = Development()
    
    
    cherrypy.quickstart(root, '/', config=config.cherrycfg)

if __name__ == '__main__':
    runserver()
