# !/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from fred_webadmin import setuplog
setuplog.setup_log()


import time
import traceback

from logging import debug, error
from cgi import escape
from copy import copy

import omniORB
from omniORB import CORBA
import CosNaming

# DNS lib imports
import dns.message
import dns.resolver
import dns.query

from fred_webadmin import config
 
# Conditional import. Business decision. User should not be forced to import
# ldap if he does not wish to use ldap authentication.
if config.auth_method == 'LDAP':
    import fred_webadmin.auth.ldap_auth as auth
elif config.auth_method == 'CORBA':
    import fred_webadmin.auth.corba_auth as auth
elif config.auth_method == 'OPENID':
    import fred_webadmin.auth.openid_auth as auth
else:
    raise Exception("No valid authentication module has been configured.")

# CherryPy main import
import cherrypy
from cherrypy.lib import http
import simplejson

import fred_webadmin.corbarecoder as recoder
import fred_webadmin.utils as utils

from fred_webadmin.logger.sessionlogger import (
    SessionLogger, SessionLoggerFailSilent, LoggingException)
from fred_webadmin.logger.dummylogger import DummyLogger, DummyLogRequest

from fred_webadmin.controller.listtable import ListTableMixin

from fred_webadmin.controller.adiferrors import (
    AuthenticationError, AuthorizationError)

# decorator for exposing methods
from fred_webadmin import exposed

# CORBA objects
from fred_webadmin.corba import Corba
corba_obj = Corba()

from fred_webadmin.corba import ccReg
from fred_webadmin.translation import _

# This must all be imported because of the way templates are dealt with.
from fred_webadmin.webwidgets.templates.pages import (
    BaseSite, BaseSiteMenu, LoginPage, DisconnectedPage, NotFound404Page, 
    AllFiltersPage, FilterPage, ErrorPage, DigPage, SetInZoneStatusPage, 
    DomainDetail, ContactDetail, NSSetDetail, KeySetDetail, RegistrarDetail, 
    ActionDetail, PublicRequestDetail, MailDetail, InvoiceDetail, LoggerDetail,
    RegistrarEdit, BankStatementPairingEdit, BankStatementDetail, 
    BankStatementDetailWithPaymentPairing
)
from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget
from fred_webadmin.webwidgets.gpyweb.gpyweb import (
    DictLookup, noesc, attr, ul, li, a, div, p)
from fred_webadmin.webwidgets.menu import MenuHoriz
from fred_webadmin.menunode import menu_tree
from fred_webadmin.webwidgets.forms.adifforms import LoginForm

# Must be imported because of template magic stuff. I think.
from fred_webadmin.webwidgets.forms.editforms import (RegistrarEditForm,
    BankStatementPairingEditForm)
import fred_webadmin.webwidgets.forms.editforms as editforms

import fred_webadmin.webwidgets.forms.filterforms as filterforms
from fred_webadmin.webwidgets.forms.filterforms import *
#from fred_webadmin.webwidgets.forms.filterforms import (
#    get_filter_forms_javascript)

from fred_webadmin.utils import json_response

from fred_webadmin.mappings import ( 
                      f_urls, 
                      f_name_actiondetailname)
from fred_webadmin.user import User

from fred_webadmin.customview import CustomView

from fred_webadmin.controller.perms import check_onperm, login_required

SESSION_OPENID_REDIRECT = "openid_redirect"


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
            # returns ClassName + Action (e.g. DomainDetail) class from 
            # module of this class, if there is no such, then it returns 
            # BaseSiteMenu: 
            template_name = self.__class__.__name__ + action.capitalize()
            debug('Snazim se vzit templatu jmenem:' + template_name)
            template = getattr(
                sys.modules[self.__module__], template_name, None)
            if template is None:
                error("TEMPLATE %s IN MODULE %s NOT FOUND, USING DEFAULT: "
                      "BaseSiteMenu" % (template_name, 
                      sys.modules[self.__module__]))
                template = BaseSiteMenu 
            else:
                debug('...OK, template %s taken' % template_name)
            if not issubclass(template, WebWidget):
                raise RuntimeError("%s is not derived from WebWidget - it "
                                   "cannot be template!" % repr(template))
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
        if config.debug:
            return '%s<br/>%s' % (str(kwd), str(params))
        else:
            return self._render('404_not_found')

    def _remove_session_data(self):
        cherrypy.session['user'] = None
        cherrypy.session['corbaSession'] = None
        cherrypy.session['corbaSessionString'] = None
        cherrypy.session['corba_server_name'] = None
        cherrypy.session['Admin'] = None
        cherrypy.session['Mailer'] = None
        cherrypy.session['FileManager'] = None
        cherrypy.session['filter_forms_javascript'] = None
        cherrypy.session['corba_logd'] = None
        cherrypy.session['filterforms'] = None


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
                
                result = filterforms.get_filter_forms_javascript(
                    cherrypy.session['filterforms'])
                cherrypy.session['filter_forms_javascript'] = result 
                return result
            elif args[0] == 'set_history':
                new_history = simplejson.loads(kwd.get('history', 'false'))
                cherrypy.session['history'] = new_history
                utils.get_corba_session().setHistory(new_history)
                debug('History set to %s' % new_history)
                return json_response(new_history)
        return super(ADIF, self).default(*args, **kwd)

    def _set_logger_page(self, logger_page_class):
        """ Remove logger from cherrypy apps tree.
        """
        cherrypy.tree.apps[''].root.logger = logger_page_class()
        
    def _create_session_logger(self):
        """ Creates logger object to send log requests to the server.
            Returns:
                Logger object. Either DummyLogger when nothing should be
                logged, or SessionLogger (normal logging with exceptions on
                failure), or SessionLoggerFailSilent (logging that fails
                silently without exceptions).
        """
        if not config.audit_log['logging_actions_enabled']:
            # Dummt object, only implements the interface.
            logger = DummyLogger()
        else:
            try:
                corba_logd = corba_obj.getObject("Logger", "Logger")
            except CosNaming.NamingContext.NotFound:
                if config.audit_log['force_critical_logging']:
                    raise
                form = filterforms.LoggerFilterForm 
                if form in cherrypy.session['filterforms']:
                    # Remove LoggerFilterForm from filterforms to prevent
                    # exceptions during filterform-related javascript 
                    # generation.
                    cherrypy.session['filterforms'].remove(form)
                self._set_logger_page(LoggerDisabled)
                logger = DummyLogger()
            else:
                self._set_logger_page(Logger)
                # CorbaLazyRequest needs to have the CORBA logd object in
                # cherrypy.session
                cherrypy.session['corba_logd'] = corba_logd
                if config.audit_log['force_critical_logging']:
                    # Logger raises exceptions on error.
                    logger = SessionLogger(dao=corba_logd)
                else:
                    # Logger ignores logging errors.
                    logger = SessionLoggerFailSilent(dao=corba_logd)
        return logger

    def _handle_double_login(self):
        debug('Already logged in, corbaSessionString = %s' % 
            cherrypy.session.get('corbaSessionString'))

    def _corba_connect(self, corba_server):
        """ Connect to corba. 
        """
        ior = config.iors[corba_server][1]
        nscontext = config.iors[corba_server][2]
        corba_obj.connect(ior, nscontext)

    def _init_login(self, form):
        login = form.cleaned_data.get('login', '')
        corba_server = int(form.cleaned_data.get('corba_server', 0))
        cherrypy.session['filterforms'] = copy(filterforms.form_classes)
        self._corba_connect(corba_server)
        logger = self._create_session_logger()
        try:
            logger.start_session("en", login)
        except (omniORB.CORBA.SystemException,
                ccReg.Admin.ServiceUnavailable):
            if config.audit_log['force_critical_logging']:
                raise
            logger = DummyLogger()
        log_req = logger.create_request(
            cherrypy.request.remote.ip, cherrypy.request.body, "Login")
        log_req.update("username", login)
        admin = corba_obj.getObject('Admin', 'Admin')
        cherrypy.session['Admin'] = admin
        cherrypy.session['Logger'] = logger
        return admin, log_req

    def _authenticate(self, form, admin, log_req):
        login = form.cleaned_data.get('login', '')
        password = form.cleaned_data.get('password', '')
        try:
            auth.authenticate_user(admin, login, password)
        except AuthenticationError, e:
            cherrypy.response.status = 403
            raise
       
    def _authorize(self, form, admin, log_req):
        login = form.cleaned_data.get('login', '')
        corbaSessionString = admin.createSession(recoder.u2c(login))
        log_req.update("session_id", corbaSessionString)
        try:
            session = admin.getSession(corbaSessionString)
            # User gets authorized for login when User object is created.
            user = User(session.getUser())
        except AuthorizationError, e:
            admin.destroySession(corbaSessionString)
            cherrypy.response.status = 403
            raise
        cherrypy.session['user'] = user
        return user, corbaSessionString

    def _fill_session_data(self, form, user, corbaSessionString):
        cherrypy.session['corbaSessionString'] = corbaSessionString
        corba_server = int(form.cleaned_data.get('corba_server', 0))
        cherrypy.session['corba_server_name'] = \
            form.fields['corba_server'].choices[corba_server][1]
        cherrypy.session['filter_forms_javascript'] = None
        cherrypy.session['filterforms'] = copy(filterforms.form_classes)
        cherrypy.session['Logger'].set_common_property("session_id", corbaSessionString)
        cherrypy.session['Mailer'] = corba_obj.getObject('Mailer', 'Mailer')
        cherrypy.session['FileManager'] = corba_obj.getObject(
            'FileManager', 'FileManager')
            
        cherrypy.session['history'] = False
        utils.get_corba_session().setHistory(False)

    def login(self, *args, **kwd):
        """ The 'gateway' to the rest of Daphne. Handles authentication and 
            login form processing."
        """
        if cherrypy.session.get('corbaSessionString'): 
            # Already logged in, redirect to /summary.
            self._handle_double_login()
            raise cherrypy.HTTPRedirect('/summary/')

        if cherrypy.session.get(SESSION_OPENID_REDIRECT):
            # OpenID redirect => get stored data from the session.
            form_data = cherrypy.session.get('login_data')['form_data']
            form = LoginForm(form_data, action='/login/', method='post')
        elif kwd:
            if cherrypy.request.method == 'GET' and kwd.get('next'):
                form = LoginForm(action='/login/', method='post')
                form.fields['next'].value = kwd['next']
            else:
                form = LoginForm(kwd, action='/login/', method='post')
        else:
            form = LoginForm(action='/login/', method='post')
        
        if form.is_valid():
            log_req = DummyLogRequest()
            try:
                log_req, admin = self._login_init_and_authenticate(form)
                user, session_string = self._authorize(form, admin, log_req)
            except cherrypy.HTTPRedirect:
                # OpenID redirect => store necessary data in the session.
                cherrypy.session['login_data'] = {}
                cherrypy.session['login_data']['log_req'] = log_req
                cherrypy.session['login_data']['form_data'] = form.cleaned_data
            except (omniORB.CORBA.BAD_PARAM, AuthenticationError, 
                    AuthorizationError), exc:
                log_req.update("result", str(exc))
                form.non_field_errors().append(str(exc))
                if config.debug:
                    form.non_field_errors().append(noesc(escape(unicode(
                        traceback.format_exc())).replace('\n', '<br/>')))
                log_req.commit()
            else:
                self._fill_session_data(form, user, session_string)
                if cherrypy.session.get('login_data'):
                    del(cherrypy.session['login_data'])
                # Login completed, go to the next page.
                raise cherrypy.HTTPRedirect(form.cleaned_data.get('next'))
            finally:
                # Set OpenID redirect to False in any case (it will be set to
                # True when it is redirected).
                cherrypy.session[SESSION_OPENID_REDIRECT] = False

        form.action = '/login/'
        return self._render('login', {'form': form})

    def _login_init_and_authenticate(self, form):
        """ Obtains CORBA admin reference either from the session data 
            (when we've been redirected by OpenID authentication) or 
            directly from the server. 
            Also obtains the login log request.
        """
        if cherrypy.session.get(SESSION_OPENID_REDIRECT):
            admin = cherrypy.session.get('Admin')
            log_req = cherrypy.session.get('login_data')['log_req']
        else:
            admin, log_req = self._init_login(form)
            # May raise a HTTPRedirect
            self._authenticate(form, admin, log_req)
        return log_req, admin

    @login_required
    def logout(self):
        if cherrypy.session.get('Admin'):
            try:
                session_string = cherrypy.session['corbaSessionString']
                cherrypy.session['Admin'].destroySession(
                    session_string)
            except CORBA.TRANSIENT, e:
                debug('Admin.destroySession call failed, backend server '
                      'is not running.\n%s' % e)
        if cherrypy.session.get('Logger'):
            try:
                req = cherrypy.session['Logger'].create_request(
                    cherrypy.request.remote.ip, cherrypy.request.body, "Logout")
                req.commit("") 
                cherrypy.session['Logger'].close_session()
            except (omniORB.CORBA.SystemException, 
                ccReg.Admin.ServiceUnavailable,
                LoggingException):
                # Let the user logout even when logging is critical (otherwise
                # they're stuck in Daphne and they have to manually delete the
                # session).
                error("Failed to log logout action!")
                pass
        self._remove_session_data()
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
    pass


class LoggerDisabled(Logger):
    """ Substitute class used instead of normal Logger when the application 
        cannot connect to CORBA logd. 
        We need to disable access to the logger from the menu. Hiding the menu
        item is not enough (the user could still use the logger URL).

        TODO: Perhaps we should rather hide the logger menu item and delete 
        the logger item from the app tree.
    """
    def __init__(self, *args, **kwargs):
        Logger.__init__(self, *args, **kwargs)

    def _get_menu_handle(self, action):
        return "logger"
        
    def filter(self, *args, **kwd):
        return self.index()

    def allfilters(self, *args, **kwd):
        return self.index()

    def detail(self, **kwd):
        return self.index()

    def index(self):
        context = DictLookup()
        context.main = p(
            "Logging has been disabled, Daphne could not connect to CORBA logd.") 
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
                log_request_name:
                    The type of log request that keeps log of this event.
        """
        context = {'main': div()}
        form_class = self._get_editform_class()
        initial = registrar.__dict__

        if cherrypy.request.method == 'POST':
            form = form_class(kwd, initial=initial, method='post')
            if form.is_valid():
                # Create the log request only after the user has clicked on
                # "save" (we only care about contacting the server, not about 
                # user entering the edit page).
                log_request = cherrypy.session['Logger'].create_request(
                    cherrypy.request.remote.ip, cherrypy.request.body, 
                    log_request_name)
                self._process_valid_form(
                    form, registrar, kwd.get('id'), context, log_request)
            else:
                if config.debug:
                    context['main'].add(
                        'Form is not valid! Errors: %s' % repr(form.errors))
        else:
            form = form_class(method='post', initial=initial)

        context['form'] = form
        return self._render('edit', context)
    
    @check_onperm('change')
    def edit(self, *params, **kwd):
        registrar = self._get_detail(obj_id=kwd.get('id'))
        result = self._update_registrar(registrar, "RegistrarUpdate", *params, **kwd)
        return result

    @check_onperm('change')
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
        except Exception, e:
            #TODO(tomas): Log an error?
            #TODO(tomas): Remove ugly legacy general exception handling.
            log_request.update("result", str(e))
            context['main'] = _("Object_not_found")
            return self._render('base', ctx=context)
        finally:
            log_request.commit("")
        context['handle'] = handle
        context['dig'] = dig
        return self._render('dig', context)

    @check_onperm('change')
    def setinzonestatus(self, **kwd):
        "Call setInzoneStatus(domainID) "
        log_request = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body, 
            "SetInZoneStatus")
        context = {'error': None}
        domain_id = kwd.get('id', None) # domain ID
        if not domain_id:
            log_request.update("result", "No domain id.")
            log_request.commit("")
            raise cherrypy.HTTPRedirect(f_urls[self.classname])        
        log_request.update("domainId", domain_id)

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
            log_request.commit("")
            # use this URL in trunk version:
            # HTTPRedirect(f_urls[self.classname] + '/detail/?id=%s' % domain_id)
            # this URL is compatible with branche 3.1
            raise cherrypy.HTTPRedirect('/domain/detail/?id=%s' % domain_id)
        
        # display domain name
        try:
            context['handle'] = admin.getDomainById(int(domain_id)).fqdn
        except Exception, e:
            context['error'] = e
        log_request.update("result", "An error has occured.")
        log_request.commit("")
        # display page with error message
        return self._render('setinzonestatus', context)


class Contact(AdifPage, ListTableMixin):
    pass

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
    @check_onperm('change')
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

        except (TypeError, ValueError), e:
            log_req.update("result", str(e))
            log_req.commit()
            context['main'] = _("Required_integer_as_parameter")
            return self._render('base', ctx=context)
        try:
            cherrypy.session.get('Admin').processPublicRequest(id_pr, False)
        except ccReg.Admin.REQUEST_BLOCKED, e:
            log_req.update("result", str(e))
            log_req.commit()
            raise CustomView(self._render(
                'error', {'message': [
                    _(u'This object is blocked, request cannot be accepted.'
                    u'You can return back to '), a(attr(
                        href=f_urls[self.classname] + 'detail/?id=%s' % id_pr), 
                        _('public request.'))]}))
            
        raise cherrypy.HTTPRedirect(f_urls[self.classname] + 'filter/?reload=1&load=1')

    @check_onperm('change')
    def close(self, **kwd):
        '''Close and invalidate'''
        context = {}
        log_req = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body,
            "PublicRequestInvalidate")
        try:
            id_ai = int(kwd.get('id'))
            log_req.update("publicrequest_id", id_ai)
            log_req.commit()
        except (TypeError, ValueError), e:
            log_req.update("result", str(e))
            log_req.commit()
            context['main'] = _("Required_integer_as_parameter")
            return self._render('base', ctx=context)
        cherrypy.session.get('Admin').processPublicRequest(id_ai, True)
        raise cherrypy.HTTPRedirect(f_urls[self.classname] + 'filter/?reload=1&load=1' % (self.classname))


class Invoice(AdifPage, ListTableMixin):
    pass


class BankStatement(AdifPage, ListTableMixin):
    def _pair_payment_with_registrar(self, context, payment_id, payment_type,
            registrar_handle):
        """ Links the payment with registrar. """
        log_req = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body, "PaymentPair")
        log_req.update("payment_id", payment_id)
        log_req.update("registrar_handle", registrar_handle)
        invoicing = utils.get_corba_session().getBankingInvoicing()
        success = True
        if payment_type == editforms.PAYMENT_REGISTRAR:
            success = invoicing.pairPaymentRegistrarHandle(
                payment_id, recoder.u2c(registrar_handle))
        success = success and invoicing.setPaymentType(
            payment_id, payment_type)
        if not success:
            log_req.update("result", "Could not pair payment")
        log_req.commit()
        return success

    @check_onperm('read')
    def detail(self, **kwd):
        """ Detail for Payment. If the payment is not paired with any
            Registrar, we display a pairing form too.
        """
        context = {}
        # Indicator whether the pairing action has been carried out
        # successfully.
        pairing_success = False

        user = cherrypy.session['user']
        user_has_change_perms = not user.check_nperms("change.bankstatement")
        
        log_req = cherrypy.session['Logger'].create_request(
            cherrypy.request.remote.ip, cherrypy.request.body, 
            f_name_actiondetailname[self.__class__.__name__.lower()])

        obj_id = kwd.get('id')
        try:
            obj_id = int(obj_id)
        except (TypeError, ValueError), e:
            log_req.update("result", str(e))
            log_req.commit()
            context['main'] = _(
                "Requires integer as parameter (got %s)." % obj_id)
            raise CustomView(self._render('base', ctx=context))
        
        # When the user sends the pairing form we arrive at BankStatement
        # detail again, but this time we receive registrar_handle in kwd
        # => pair the payment with the registrar.
        if cherrypy.request.method == 'POST' and user_has_change_perms:
            registrar_handle = kwd.get('handle', None)
            payment_type = kwd.get('type', None)
            try:
                payment_type = int(payment_type)
            except (TypeError, ValueError), e:
                log_req.update("result", str(e))
                log_req.commit()
                context['main'] = _(
                    "Requires integer as parameter (got %s)." % payment_type)
                raise CustomView(self._render('base', ctx=context))
            pairing_success = self._pair_payment_with_registrar(
                context, obj_id, payment_type, registrar_handle)

        # Do not use cache - we want the updated BankStatementItem.
        detail = utils.get_detail(self.classname, obj_id, use_cache=False)
        log_req.update('object_id', kwd.get('id'))
        context['detail'] = detail 
        context['form'] = BankStatementPairingEditForm(
            method="POST",
            initial={
                'handle': kwd.get('handle', None),
                'statementId': kwd.get('statementId', None),
                'type': kwd.get('type', 2),
                'id': obj_id},
            onsubmit='return confirmAction();')
        if cherrypy.request.method == 'POST' and not pairing_success:
            # Pairing form was submitted, but pairing did not finish
            # successfully => Show an error.
            context['form'].non_field_errors().append(
                """Could not pair. Perhaps you have entered"""
                """ an invalid handle?""")
        log_req.commit("")
        
        if detail.type == editforms.PAYMENT_UNASSIGNED and user_has_change_perms:
            # Payment not paired => show the payment pairing edit form
            action = 'pair_payment'
            # invoiceId is a link to detail, but for id == 0 this detail does
            # not exist => hide invoiceId value so the link is not "clickable".
            # Note: No information is lost, because id == 0 semantically means 
            # that there is no id.
            context['detail'].invoiceId = ""
        else:
            action = 'detail'
            if detail.type != editforms.PAYMENT_REGISTRAR:
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
            raise RuntimeError(
                "%s is not derived from WebWidget - it "
                "cannot be a template!" % repr(template))
        return template


class Filter(AdifPage, ListTableMixin):
    def _get_menu_handle(self, action):
        return 'summary'

   
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
            "request.params: '%s'" % cherrypy.request.params,
            "request.wsgi_environ: '%s'" % cherrypy.request.wsgi_environ,
            "params: %s" % str(params),
            "kwd: %s" % str(kwd),
            "config: '%s'" % cherrypy.config,
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
        h = hpy()
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

class OpenID(AdifPage):
    def index(self):
        cherrypy.session[SESSION_OPENID_REDIRECT] = True
#        raise cherrypy.HTTPRedirect("/login")
        return cherrypy.session['openid_form']

    def _normalize_dict(self, args):
        normal = {}
        for key, value in args:
            try:
                prefix, rest = key.split('.', 1)
                if prefix != 'openid':
                    normal[str(key)] = value
            except ValueError: #no prefix
                normal[str(key)] = value
        return normal

    def process(self, *args, **kwargs):
        from openid.store import memstore
        from openid.consumer import consumer
        store = memstore.MemoryStore()
        query = {}
        for k, v in kwargs.items():
            query[k] = v.decode('utf-8')
        cons = consumer.Consumer(cherrypy.session['openid_session'], store)
        import ipdb; ipdb.set_trace()
        res = cons.complete(query, cherrypy.url("/") + "openid/process")
#        res = cons.complete(cons.session, cherrypy.url("/") + "openid/process")
        return res.message


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


def prepare_root():
    root = ADIF()
    root.detail41 = Detail41()
    root.summary = Summary()
    if config.audit_log['viewing_actions_enabled']:
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
    root.openid = OpenID()

    return root

def runserver(root):
    print "-----====### STARTING ADIF ###====-----"
    cherrypy.quickstart(root, '/', config=config.cherrycfg)

if __name__ == '__main__':
    root = prepare_root()
    runserver(root)
