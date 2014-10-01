# !/usr/bin/python
# -*- coding: utf-8 -*-

import sys

if sys.version_info >= (2, 7):
    from collections import OrderedDict
else:
    from fred_webadmin.utils import OrderedDict

from fred_webadmin import setuplog
setuplog.setup_log()


import time
import traceback

from logging import debug, error
from cgi import escape
from copy import copy, deepcopy

import omniORB
from omniORB import CORBA

# DNS lib imports
import dns.message
import dns.resolver
import dns.query

from fred_webadmin import config
from fred_webadmin import messages

# Conditional import. Business decision. User should not be forced to import
# ldap if he does not wish to use ldap authentication.
if config.auth_method == 'LDAP':
    import fred_webadmin.auth.ldap_auth as auth
elif config.auth_method == 'CORBA':
    import fred_webadmin.auth.corba_auth as auth
else:
    raise Exception("No valid authentication module has been configured.")

# CherryPy main import
import cherrypy
from cherrypy.lib import http
import simplejson

import fred_webadmin.corbarecoder as recoder
from fred_webadmin import utils

import fred_webadmin.webwidgets.forms.fields as formfields

from pylogger.corbalogger import LoggingException
from pylogger.dummylogger import DummyLogger

from fred_webadmin.controller.listtable import ListTableMixin

from fred_webadmin.controller.adiferrors import (
    AuthenticationError, AuthorizationError)

# decorator for exposing methods
from fred_webadmin import exposed

# CORBA objects
from fred_webadmin.corba import Corba
corba_obj = Corba()

from fred_webadmin.corba import ccReg, Registry
from fred_webadmin.translation import _

# This must all be imported because of the way templates are dealt with.
from fred_webadmin.webwidgets.templates.pages import (BaseSiteMenu,
    DomainBlocking, DomainBlockingResult, BankStatementDetailWithPaymentPairing, GroupEditorPage)
from fred_webadmin.webwidgets.gpyweb.gpyweb import (
    DictLookup, noesc, attr, ul, li, a, div, p)


from fred_webadmin.webwidgets.forms.adifforms import LoginForm

# Must be imported because of template magic stuff. I think.
from fred_webadmin.webwidgets.forms.editforms import (RegistrarEditForm,
    BankStatementPairingEditForm, GroupManagerEditForm)
import fred_webadmin.webwidgets.forms.editforms as editforms

import fred_webadmin.webwidgets.forms.filterforms as filterforms
from fred_webadmin.webwidgets.forms.filterforms import *

from fred_webadmin.utils import json_response
from fred_webadmin.mappings import f_urls
from fred_webadmin.user import User
from fred_webadmin.customview import CustomView
from fred_webadmin.controller.perms import check_onperm, login_required
from fred_webadmin.controller.administrative_blocking import (ProcessBlockView, ProcessUpdateBlockingView,
    ProcessUnblockView, ProcessBlacklistAndDeleteView)
from . import administrative_verification
from base import AdifPage


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
            elif args[0] == 'service_actions.js':
                result = filterforms.get_service_actions_javascript(
                    cherrypy.session.get("Logger"))
                return result
        return super(ADIF, self).default(*args, **kwd)

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
        corba_server_spec = int(form.cleaned_data.get('corba_server', 0))
        cherrypy.session['corba_server'] = corba_server_spec  # couple [oir, context]
        cherrypy.session['filterforms'] = copy(filterforms.form_classes)
        self._corba_connect(corba_server_spec)

        admin = corba_obj.getObject('Admin', 'ccReg.Admin')
        cherrypy.session['Admin'] = admin

        logger = utils.get_logger()
        if getattr(logger, 'dao', None):
            cherrypy.session['Logger'] = logger.dao  # needed by CorbaLazyRequest
        if isinstance(logger, DummyLogger):
            logger_form = filterforms.LoggerFilterForm
            if logger_form in cherrypy.session['filterforms']:
                # Remove LoggerFilterForm from filterforms to prevent
                # exceptions during filterform-related javascript
                # generation.
                cherrypy.session['filterforms'].remove(logger_form)
        return admin

    def _authenticate(self, form, admin):
        login = form.cleaned_data.get('login', '')
        password = form.cleaned_data.get('password', '')
        logger = utils.get_logger()
        try:
            auth.authenticate_user(admin, login, password)
            try:
                logger_session_id = logger.start_session(0, login)
                cherrypy.session['logger_session_id'] = logger_session_id
            except (omniORB.CORBA.SystemException,
                    ccReg.Admin.ServiceUnavailable):
                if config.audit_log['force_critical_logging']:
                    raise
        except AuthenticationError:
            cherrypy.response.status = 403
            raise

    def _authorize(self, form, admin):
        login = form.cleaned_data.get('login', '')
        corbaSessionString = admin.createSession(recoder.u2c(login))
        try:
            session = admin.getSession(corbaSessionString)
            # User gets authorized for login when User object is created.
            user = User(session.getUser())
        except AuthorizationError:
            admin.destroySession(corbaSessionString)
            cherrypy.response.status = 403
            raise
        cherrypy.session['user'] = user
        return user, corbaSessionString

    def _fill_session_data(self, form, user, corbaSessionString):
        cherrypy.session['corbaSessionString'] = corbaSessionString
        corba_server = int(form.cleaned_data.get('corba_server', 0))
        cherrypy.session['corba_server_name'] = form.fields['corba_server'].choices[corba_server][1]
        cherrypy.session['filter_forms_javascript'] = None

        cherrypy.session['Mailer'] = corba_obj.getObject('Mailer', 'ccReg.Mailer')
        cherrypy.session['FileManager'] = corba_obj.getObject('FileManager', 'ccReg.FileManager')
        cherrypy.session['Messages'] = corba_obj.getObject('Messages', 'Registry.Messages')
        cherrypy.session['Blocking'] = corba_obj.getObject('AdminBlocking', 'Registry.Administrative.Blocking')
        cherrypy.session['Verification'] = corba_obj.getObject('AdminContactVerification', 'Registry.AdminContactVerification.Server')

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

        if kwd:
            if cherrypy.request.method == 'GET' and kwd.get('next'):
                form = LoginForm(action='/login/', method='post')
                form.fields['next'].value = kwd['next']
            else:
                form = LoginForm(kwd, action='/login/', method='post')
        else:
            form = LoginForm(action='/login/', method='post')

        if form.is_valid():
            admin = self._init_login(form)
            log_req = utils.create_log_request('Login', [['username', form.cleaned_data.get('login')]])
            out_props = []
            try:
                # May raise a HTTPRedirect
                self._authenticate(form, admin)
                user, corba_session_string = self._authorize(form, admin)
                out_props.append(['session_id', corba_session_string])
                log_req.result = 'Success'
            except (AuthenticationError, AuthorizationError), exc:
                form.non_field_errors().append(str(exc))
                if config.debug:
                    form.non_field_errors().append(noesc(escape(unicode(
                        traceback.format_exc())).replace('\n', '<br/>')))
                if log_req:
                    log_req.result = 'Fail'
                self._remove_session_data()
            else:
                self._fill_session_data(form, user, corba_session_string)
                if log_req:
                    log_req.result = 'Success'
                # Login completed, go to the next page.
                raise cherrypy.HTTPRedirect(form.cleaned_data.get('next', "/summary/"))
            finally:
                if log_req:
                    log_req.close(properties=out_props, session_id=cherrypy.session.get('logger_session_id', 0))

        form.action = '/login/'
        return self._render('login', {'form': form})

    @login_required
    def logout(self):
        if cherrypy.session.get('Admin'):
            try:
                corba_session_string = cherrypy.session['corbaSessionString']
                cherrypy.session['Admin'].destroySession(
                    corba_session_string)
            except CORBA.TRANSIENT, e:
                debug('Admin.destroySession call failed, backend server '
                      'is not running.\n%s' % e)
        if cherrypy.session.get('Logger'):
            try:
                log_req = utils.create_log_request('Logout')
                log_req.result = 'Success'
                log_req.close()
                utils.get_logger().close_session(session_id=cherrypy.session.get('logger_session_id'))
            except (omniORB.CORBA.SystemException,
                ccReg.Admin.ServiceUnavailable,
                LoggingException):
                # Let the user logout even when logging is critical (otherwise
                # they're stuck in Daphne and they have to manually delete the
                # session).
                error("Failed to log logout action!")
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
            lambda x: ccReg.AdminZoneAccess(**x), val)
        self.type_transformer['access'] = lambda val: map(
            lambda x: ccReg.AdminEPPAccess(**x), val)
        self.type_transformer['id'] = lambda val: int(val)

    def _get_empty_corba_struct(self):
        """ Creates a ccReg.AdminRegistrar object representing
            a new registrar to be created on server side. """
        new = []
        new.append(0)  # id
        new.extend([''] * 3)
        new.append(False)  # vat
        new.extend([''] * 9)
        admin = cherrypy.session.get('Admin')
        new.extend([admin.getDefaultCountry()])
        new.extend([''] * 4)
        new.append('')  # money
        new.append([])  # accesses
        new.append([])  # active zones
        new.append(False)  # hidden
        return ccReg.AdminRegistrar(*new)  # empty registrar

    def _fill_registrar_struct_from_form(self, registrar, cleaned_data):
        result = deepcopy(registrar)
        for field_key, field_val in cleaned_data.items():
            # Create the corba object for the respective field.
            if field_key in self.type_transformer:
                corba_val = self.type_transformer[field_key](field_val)
            else:
                corba_val = field_val
            setattr(result, field_key, corba_val)
        return result

    def _get_changed_fields_formset(self, formset, name, props):
        for form in formset.forms:
            if form.has_changed():
                for key, field in form.fields.items():
                    if isinstance(field, formfields.FileField):
                        if field.value and field.value.filename:
                            props.append(("set_%s" % key, field.value.filename, True))
                    else:
                        props.append(("set_%s" % key, field.value, True))

    def _construct_changed_fields(self, form):
        props = []
        if form.has_changed:
            data = form.changed_data
            for field_name in data:
                field = form.fields[field_name]
                if getattr(field, "formset", False):
                    self._get_changed_fields_formset(field.formset, field_name, props)
                else:
                    props.append(("set_%s" % field_name, field.value))
        return props

    def _process_valid_form(self, form, reg, reg_id,
                            context, log_request_name):
        props = self._construct_changed_fields(form)
        in_refs = []
        if reg_id:
            in_refs = [('registrar', int(reg_id))]
        log_req = utils.create_log_request(log_request_name, properties=props, references=in_refs)
        out_refs = []
        try:
            registrar = self._fill_registrar_struct_from_form(reg, form.cleaned_data)

            corba_reg = recoder.u2c(registrar)

            result = {'reg_id': None}
            form.fire_actions(updated_registrar=corba_reg, result=result)
            if result['reg_id'] != reg_id:  # new registrar created, add him to out_refs
                out_refs.append(('registrar', result['reg_id']))
            reg_id = result['reg_id']
            log_req.result = 'Success'
        except editforms.UpdateFailedError, e:
            form.non_field_errors().append(str(e))
            context['form'] = form
            log_req.result = 'Fail'
            return context
        finally:
            log_req.close(references=out_refs)
        # Jump to the registrar's detail.
        raise cherrypy.HTTPRedirect('/registrar/detail/?id=%s' % reg_id)

    def _update_registrar(self, registrar, log_request_name, action_is_edit, *params, **kwd):
        """ Handles the actual updating/creating of a registrar.

            Note that we have to "glue" the registrar initial form data
            together. This is unfortunate, but it's caused by the design
            of IDL.

            Args:
                registrar:
                    The ccReg.AdminRegistrar object that is being updated or
                    created.
                log_request_name:
                    The type of log request that keeps log of this event.
                action_is_edit:
                    True iff we are editing an already existing registrar.
                    false iff we are creating a new one.
        """
        context = {'main': div()}
        reg_data_form_class = self._get_editform_class()
        reg_data_initial = registrar.__dict__
        initial = reg_data_initial
        if action_is_edit:
            # Only append groups and certifications when we're editing an
            # already existing registrar (there are none for a new registrar).
            groups = self._get_groups_for_reg_id(int(kwd.get('id')))
            initial['groups'] = recoder.c2u(groups)
            certs = self._get_certifications_for_reg_id(int(kwd.get('id')))
            initial['certifications'] = recoder.c2u(certs)

        if cherrypy.request.method == 'POST':
            form = reg_data_form_class(kwd, initial=initial, method='post')
            if form.is_valid():
                # Create the log request only after the user has clicked on
                # "save" (we only care about contacting the server, not about
                # user entering the edit page).

                context = self._process_valid_form(
                    form, registrar, kwd.get('id'), context, log_request_name)
                return context
            else:
                if config.debug:
                    context['main'].add(
                        'Form is not valid! Errors: %s' % repr(form.errors))
        else:
            form = reg_data_form_class(method='post', initial=initial)

        context['form'] = form
        return context

    @check_onperm('read')
    def detail(self, **kwd):
        log_req = self._create_log_req_for_object_view(**kwd)
        context = {}
        try:
            detail = self._get_detail(obj_id=kwd.get('id'))
            if detail is None:
                log_req.result = 'Fail'
            else:
                log_req.result = 'Success'

            result = detail.__dict__
            result['groups'] = (
                recoder.c2u(self._get_groups_for_reg_id(int(kwd.get('id')))))
            result['certifications'] = (
                recoder.c2u(
                    self._get_certifications_for_reg_id(int(kwd.get('id')))))
            ###TODO: This is here temporarily till backandist will create interface for blokcing registrars with history
            admin = cherrypy.session.get('Admin')
            result['is_blocked'] = admin.isRegistrarBlocked(int(kwd.get('id')))
            ### ==

            context['edit'] = kwd.get('edit', False)
            context['result'] = result
        finally:
            log_req.close()
        return self._render('detail', context)

    def _get_groups_for_reg_id(self, reg_id):
        """ Returns groups that the registrar with reg_id belongs to under the
            condition that their membership toDate value is not set (i.e., the
            membership is active).
        """
        group_mgr = cherrypy.session['Admin'].getGroupManager()
        all_groups = group_mgr.getGroups()
        memberships = group_mgr.getMembershipsByRegistar(reg_id)
        my_groups_ids = [
            member.group_id for member in recoder.c2u(memberships)
            if not member.toDate
            #or (member.toDate and not member.toDate <= datetime.date.today())
            # Note: toDate should not be in the future (webadmin allow only setting it to today), so
            # it's safe to say that if there is toDate filled, registrar is already removed from
            # the group. The only problem is that commandline fred_admin allow to set the toDate to the
            # future, so it can couse some problems (then we would have to display such group but
            # without possibility to remove it)
        ]
        groups = [group for group in all_groups if group.id in my_groups_ids]
        return groups

    def _get_certifications_for_reg_id(self, reg_id):
        cert_mgr = cherrypy.session['Admin'].getCertificationManager()
        certs = cert_mgr.getCertificationsByRegistrar(reg_id)
        return certs

    @check_onperm('change')
    def edit(self, *params, **kwd):
        registrar = self._get_detail(obj_id=kwd.get('id'))
        ctx = self._update_registrar(
            registrar, "RegistrarUpdate", action_is_edit=True, *params, **kwd)
        return self._render('edit', ctx)

    @check_onperm('change')
    def create(self, *params, **kwd):
        registrar = self._get_empty_corba_struct()
        ctx = self._update_registrar(
            registrar, "RegistrarCreate", action_is_edit=False, *params, **kwd)
        return self._render('edit', ctx)

    @check_onperm('unblock')
    def unblock(self, registrar_id):
        context = DictLookup()
        try:
            reg_id = int(registrar_id)
        except (TypeError, ValueError):
            context.message = _("Required_integer_as_parameter")
            raise CustomView(self._render('error', ctx=context))

        return_message = [
            _(u'You can return back to '),
            a(attr(href=f_urls[self.classname] + 'detail/?id=%s' % reg_id),
              _('registrar.'))
        ]

        admin = cherrypy.session.get('Admin')
        if not admin.isRegistrarBlocked(reg_id):
            context.message = [_("This registrar is not blocked.")] + return_message
            return self._render('error', ctx=context)
        else:
            log_req = utils.create_log_request('RegistrarUpdate', [['blocked', 'False']], [[self.classname, reg_id]])
            try:
                admin.unblockRegistrar(reg_id, log_req.request_id)
                log_req.result = 'Success'
            finally:
                log_req.close()

            context.main = [_("Registrar successfully unblocked.")] + return_message
            return self._render('base', ctx=context)


class Domain(AdifPage, ListTableMixin):
    blockable = True
    blocking_views = OrderedDict((
        # blocking_action: blocking view_class
        ('block', ProcessBlockView),
        ('change_blocking', ProcessUpdateBlockingView),
        ('unblock', ProcessUnblockView),
        ('blacklist_and_delete', ProcessBlacklistAndDeleteView),
        #('unblacklist_and_create', DomainUnblacklistAndCreateView),
    ))

    @check_onperm('read')
    def dig(self, **kwd):
        context = {}
        handle = kwd.get('handle', None)
        if not handle:
            raise cherrypy.HTTPRedirect(f_urls[self.classname])
        log_req = utils.create_log_request('DomainDig', properties=[("handle", handle)])
        try:
            query = dns.message.make_query(handle, 'ANY')
            resolver = dns.resolver.get_default_resolver().nameservers[0]
            dig = dns.query.udp(query, resolver).to_text()
            log_req.result = 'Success'
        except Exception:
            #TODO(tomas): Log an error?
            #TODO(tomas): Remove ugly legacy general exception handling.
            context['main'] = _("Object_not_found")
            return self._render('base', ctx=context)
        finally:
            log_req.close()
        context['handle'] = handle
        context['dig'] = dig
        return self._render('dig', context)

    @check_onperm('change')
    def setinzonestatus(self, **kwd):
        'Call setInzoneStatus(domainID)'
        log_req = self._create_log_req_for_object_view('SetInZoneStatus', **kwd)
        domain_id = kwd['id']
        context = {'error': None}
        try:
            admin = cherrypy.session.get('Admin')
            if hasattr(admin, 'setInZoneStatus'):
                try:
                    context['success'] = admin.setInZoneStatus(int(domain_id))
                # TODO(tom): Do not catch generic exception here!
                except Exception, e:
                    context['error'] = e
            else:
                context['error'] = _("Function setInZoneStatus() is not implemented in Admin.")

            # if it was successful, redirect into domain detail
            if context['error'] is None:
                log_req.result = 'Success'
                raise cherrypy.HTTPRedirect(f_urls[self.classname] + '/detail/?id=%s' % domain_id)
            else:
                log_req.result = 'Fail'
            # display domain name
            try:
                context['handle'] = utils.get_detail(self.classname, int(domain_id), use_cache=False).handle
            except Exception, e:
                context['error'] = e

            # display page with error message
            return self._render('setinzonestatus', context)
        finally:
            log_req.close()

    def _template(self, action=''):
        if action == 'blocking':
            return DomainBlocking
        elif action == 'blocking_result':
            return DomainBlockingResult
        else:
            return AdifPage._template(self, action=action)

    @check_onperm('block')
    def blocking(self, *args, **kwd):
        # from fred_webadmin.tests.webadmin.test_administrative_blocking import mock_blocking
        # mock_blocking()

        if args and args[0] == 'result':
            return self._blocking_result()

        pre_blocking_form_data = cherrypy.session.get('pre_blocking_form_data')
        if not pre_blocking_form_data:
            return self._render('error', {'message': [_(u'This page is accessible only by posting a blocking form.')]})
        else:
            blocking_view = self.blocking_views[pre_blocking_form_data['blocking_action']]
            initial = {'objects': pre_blocking_form_data['object_selection'],
                       'blocking_action': pre_blocking_form_data['blocking_action'],
            }
            context = blocking_view.as_view(initial=initial)()

            return self._render('blocking', ctx=context)

    def _blocking_result(self):
        context = {}
        if cherrypy.session.get('blocking_result'):
            blocking_result = cherrypy.session['blocking_result']
            if blocking_result.get('blocked_objects'):
                context['detail_url'] = f_urls[self.classname] + 'detail/?id=%s'
                context['heading'] = 'Result of: %s' % \
                    self.blocking_views[blocking_result['blocking_action']].action_name

                try:  # HACK: till backend return list of handle:id of changed/deleted domains, we must use history for deleted domains:
                    if blocking_result['blocking_action'] == 'blacklist_and_delete':
                        # we must turn on history flag to get details of deleted domains
                        utils.get_corba_session().setHistory(True)
                    object_details = [utils.get_detail(self.classname, object_id)
                                      for object_id in blocking_result['blocked_objects']]
                finally:
                    if blocking_result['blocking_action'] == 'blacklist_and_delete':
                        # restore history flag in backend
                        utils.get_corba_session().setHistory(cherrypy.session['history'])

                if blocking_result['blocking_action'] == 'block' and blocking_result.get('return_value'):
                    holder_changes = {}
                    for domain_holder_change in blocking_result['return_value']:
                        holder_change = {
                            'old_holder': {
                                'handle': domain_holder_change.oldOwnerHandle,
                                'link': f_urls['contact'] + 'detail/?id=%s' % domain_holder_change.oldOwnerId,
                            },
                            'new_holder': {
                                'handle': domain_holder_change.newOwnerHandle,
                                'link': f_urls['contact'] + 'detail/?id=%s' % domain_holder_change.newOwnerId,
                            }
                        }
                        holder_changes[domain_holder_change.domainId] = holder_change
                    context['holder_changes'] = holder_changes
                context['blocked_objects'] = object_details

            del cherrypy.session['blocking_result']
        else:
            context['heading'] = _('The result page has expired.')
        return self._render('blocking_result', ctx=context)


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
        log_req = self._create_log_req_for_object_view(**kwd)
        context = {}
        try:
            file_id = int(kwd['id'])
            response = cherrypy.response
            filemanager = cherrypy.session.get('FileManager')
            info = filemanager.info(recoder.u2c(file_id))
            try:
                f = filemanager.load(recoder.u2c(file_id))
                body = ''
                while 1:
                    part = f.download(102400)  # 100kBytes
                    if part:
                        body = '%s%s' % (body, part)
                    else:
                        break
                response.body = body
                response.headers['Content-Type'] = info.mimetype
                cd = '%s; filename=%s' % ('attachment', info.name)
                response.headers["Content-Disposition"] = cd
                response.headers['Content-Length'] = info.size
                log_req.result = 'Success'
            except ccReg.FileManager.FileNotFound:
                log_req.result = 'Fail'
                context['main'] = _("Object_not_found")
                return self._render('file', ctx=context)
        finally:
            log_req.close()
        return response.body


class PublicRequest(AdifPage, ListTableMixin):
    @check_onperm('change')
    def resolve(self, **kwd):
        '''Accept and send'''
        log_req = self._create_log_req_for_object_view('PublicRequestAccept', **kwd)
        try:
            cherrypy.session['Admin'].processPublicRequest(int(kwd['id']), False)
            log_req.result = 'Success'
        except ccReg.Admin.REQUEST_BLOCKED:
            log_req.result = 'Fail'
            raise CustomView(self._render(
                'error', {'message': [
                    _(u'This object is blocked, request cannot be accepted.'
                    u'You can return back to '), a(attr(
                        href=f_urls[self.classname] + 'detail/?id=%s' % kwd['id']),
                        _('public request.'))
            ]}))
        finally:
            log_req.close()

        raise cherrypy.HTTPRedirect(f_urls[self.classname] + 'filter/?reload=1&load=1')

    @check_onperm('change')
    def close(self, **kwd):
        '''Close and invalidate'''
        log_req = self._create_log_req_for_object_view('PublicRequestInvalidate', **kwd)
        try:
            cherrypy.session['Admin'].processPublicRequest(int(kwd['id']), True)
            log_req.result = 'Success'
        except ccReg.Admin.REQUEST_BLOCKED:
            log_req.result = 'Fail'
            raise CustomView(self._render(
                'error', {'message': [
                    _(u'Request cannot be accepted.'
                    u'You can return back to '), a(attr(
                        href=f_urls[self.classname] + 'detail/?id=%s' % kwd['id']),
                        _('public request.'))
            ]}))
        finally:
            log_req.close()

        raise cherrypy.HTTPRedirect(f_urls[self.classname] + 'filter/?reload=1&load=1')

    @check_onperm('change')
    def resend(self, pr_type, **kwd):
        '''Resend associated message with public request, works only with serveral public request types'''
        backend = cherrypy.session['Admin']
        backend_call_switch = {
            Registry.PublicRequest.PRT_MOJEID_CONTACT_IDENTIFICATION._n: backend.resendPin3Letter,
            Registry.PublicRequest.PRT_CONTACT_IDENTIFICATION._n: backend.resendPin3Letter,
            Registry.PublicRequest.PRT_MOJEID_CONTACT_CONDITIONAL_IDENTIFICATION._n: backend.resendPin2SMS,
            Registry.PublicRequest.PRT_CONTACT_CONDITIONAL_IDENTIFICATION._n: backend.resendPin2SMS,
        }
        log_req = self._create_log_req_for_object_view('PublicRequestResendMessage', **kwd)
        try:
            method = backend_call_switch.get(pr_type)
            if method:
                method(int(kwd['id']))
                log_req.result = 'Success'
                messages.success(_('Message was succesfully enqueued for re-send.'))
            else:
                log_req.result = 'Fail'
                messages.error(_('Invalid public request type.'))

        except ccReg.Admin.OBJECT_NOT_FOUND:
            log_req.result = 'Fail'
            messages.error(_(u'Associated message cannot be resend because request was already processed or has not valid type.'))
        except ccReg.Admin.MessageCopyProhibited:
            log_req.result = 'Fail'
            messages.error(_(u'Message cannot be re-send because it is still in queue.'))
        finally:
            log_req.close()

        raise cherrypy.HTTPRedirect(f_urls[self.classname] + 'detail/?id=%s' % kwd['id'])


class Invoice(AdifPage, ListTableMixin):
    pass


class BankStatement(AdifPage, ListTableMixin):
    def _pair_payment_with_registrar(self, payment_id, payment_type, registrar_handle):
        """ Links the payment with registrar. """
        props = [("registrar_handle", registrar_handle)]
        log_req = self._create_log_req_for_object_view('PaymentPair', properties=props, **{'id': str(payment_id)})
        try:
            invoicing = utils.get_corba_session().getBankingInvoicing()
            success = True
            if payment_type == editforms.PAYMENT_REGISTRAR:
                success = invoicing.pairPaymentRegistrarHandle(payment_id, recoder.u2c(registrar_handle))

            success = success and invoicing.setPaymentType(payment_id, payment_type)
            if success:
                log_req.result = 'Success'
            else:
                log_req.result = 'Fail'
        finally:
            log_req.close()
        return success

    @check_onperm('read')
    def detail(self, **kwd):
        """ Detail for Payment. If the payment is not paired with any
            Registrar, we display a pairing form too.
        """

        log_req = self._create_log_req_for_object_view(**kwd)
        try:
            obj_id = int(kwd.get('id'))
            context = {}
            # Indicator whether the pairing action has been carried out
            # successfully.
            pairing_success = False

            user = cherrypy.session['user']
            user_has_change_perms = not user.check_nperms("change.bankstatement")

            # When the user sends the pairing form we arrive at BankStatement
            # detail again, but this time we receive registrar_handle in kwd
            # => pair the payment with the registrar.
            if cherrypy.request.method == 'POST' and user_has_change_perms:
                registrar_handle = kwd.get('handle', None)
                payment_type = kwd.get('type', None)
                try:
                    payment_type = int(payment_type)
                except (TypeError, ValueError):
                    log_req.result = 'Fail'
                    context['main'] = _('Requires integer as parameter (got %s).' % payment_type)
                    raise CustomView(self._render('base', ctx=context))
                pairing_success = self._pair_payment_with_registrar(obj_id, payment_type, registrar_handle)

            # Do not use cache - we want the updated BankStatementItem.
            detail = utils.get_detail(self.classname, int(obj_id), use_cache=False)
            context['detail'] = detail
            context['form'] = BankStatementPairingEditForm(
                method="POST",
                initial={
                    'handle': kwd.get('handle', None),
                    'statementId': kwd.get('statementId', None),
                    'type': kwd.get('type', 2),
                },
                onsubmit='return confirmAction();')
            if cherrypy.request.method == 'POST' and not pairing_success:
                # Pairing form was submitted, but pairing did not finish
                # successfully => Show an error.
                context['form'].non_field_errors().append(
                    'Could not pair. Perhaps you have entered an invalid handle?')

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
            log_req.result = 'Success'
        finally:
            log_req.close()
        return res

    def _template(self, action=''):
        if action == "pair_payment":
            # Show detail with payment pairing form.
            return BankStatementDetailWithPaymentPairing
        else:
            # Show normal detail.
            return super(BankStatement, self)._template(action)


class Message(AdifPage, ListTableMixin):
    pass


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


# # TODO(Tom): OpenID auth does not work yet...
# class OpenID(AdifPage):
#     def index(self, *args, **kwargs):
#         cherrypy.session[SESSION_OPENID_REDIRECT] = True
# #        raise cherrypy.HTTPRedirect("/login")
#         return cherrypy.session['openid_form']
#
#     def _normalize_dict(self, args):
#         normal = {}
#         for key, value in args:
#             try:
#                 prefix, rest = key.split('.', 1)
#                 if prefix != 'openid':
#                     normal[str(key)] = value
#             except ValueError: #no prefix
#                 normal[str(key)] = value
#         return normal
#
#     def process(self, *args, **kwargs):
#         from openid.store import memstore
#         from openid.consumer import consumer
#         store = memstore.MemoryStore()
#         query = {}
#         for k, v in kwargs.items():
#             query[k] = v.decode('utf-8')
#         cons = consumer.Consumer(cherrypy.session['openid_session'], store)
#         res = cons.complete(query, cherrypy.url("/") + "openid/process")
# #        res = cons.complete(cons.session, cherrypy.url("/") + "openid/process")
#         return res.message


class Group(AdifPage):
    """ Registrar group editor page. Allows creating/deleting/renaming
        registrar groups.
    """
    @check_onperm('change')
    def index(self, *args, **kwargs):
        context = {'main': div()}
        reg_mgr = cherrypy.session['Admin'].getGroupManager()
        corba_groups = reg_mgr.getGroups()
        groups = recoder.c2u(corba_groups)
        active_groups = [group for group in groups if not group.cancelled]
        initial = {"groups": active_groups}
        if cherrypy.request.method == 'POST':
            form = GroupManagerEditForm(kwargs, initial=initial, method='post')
            if form.is_valid():
                context = self._process_valid_form(form, context)
            else:
                context['form'] = form
        else:
            form = GroupManagerEditForm(initial=initial, method='post')
            context['form'] = form
        res = self._render(action="edit", ctx=context)
        return res

    def _process_valid_form(self, form, context):
        try:
            form.fire_actions()
        except editforms.UpdateFailedError, e:
            form.non_field_errors().append(str(e))
            context['form'] = form
            return context
        raise cherrypy.HTTPRedirect(f_urls[self.classname])

    def _get_menu_handle(self, action):
        return "registrar"

    def _template(self, action=''):
        return GroupEditorPage


def prepare_root():
    root = ADIF()
    root.summary = Summary()
    if config.audit_log['viewing_actions_enabled']:
        root.logger = Logger()
    root.registrar = Registrar()
    root.domain = Domain()
    root.contact = Contact()
    root.nsset = NSSet()
    root.keyset = KeySet()
    root.mail = Mail()
    root.file = File()
    root.publicrequest = PublicRequest()
    root.invoice = Invoice()
    root.bankstatement = BankStatement()
    root.message = Message()
    root.filter = Filter()
    root.statistic = Statistics()
    root.devel = Development()
    root.group = Group()
    root.contactcheck = administrative_verification.ContactCheck()

    return root


def runserver(root):
    print "-----====### STARTING ADIF ###====-----"
    cherrypy.quickstart(root, '/', config=config.cherrycfg)

if __name__ == '__main__':
    runserver(prepare_root())
