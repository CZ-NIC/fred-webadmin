import datetime
import json

import cherrypy

from .base import AdifPage
from fred_webadmin.cache import cache
from fred_webadmin import config
from fred_webadmin.controller.perms import check_nperm, check_nperm_func, login_required
from fred_webadmin.corba import Registry, ccReg
from fred_webadmin.corbarecoder import c2u, u2c
from fred_webadmin.customview import CustomView
from fred_webadmin.enums import ContactCheckEnums, get_status_action
from fred_webadmin.mappings import f_urls
from fred_webadmin import messages
from fred_webadmin.translation import _
from fred_webadmin.utils import create_log_request, get_detail
from fred_webadmin.webwidgets.details.administrative_verification import VerificationCheckDetail
from fred_webadmin.webwidgets.forms.forms import Form
from fred_webadmin.webwidgets.forms.fields import ChoiceField
from fred_webadmin.webwidgets.gpyweb.gpyweb import DictLookup, a, attr, img
from fred_webadmin.webwidgets.simple_table import SimpleTable
from fred_webadmin.webwidgets.templates.pages import ContactCheckList, ContactCheckDetail

RESOLVE_LOCK_CACHE_KEY = 'admin_verification_resolve_%s'


class ContactCheck(AdifPage):
    SETTABLE_TEST_STATUSES = ('ok', 'fail')
    OK_TEST_STATUSES = ('ok', 'skipped')
    FAIL_TEST_STATUSES = ('fail',)
    FINAL_CHECK_STATUSES = ('ok', 'fail', 'invalidated')
    PRE_RUN_CHECK_STATUSES = ('enqueued', 'running')
    UNCLOSABLE_CHECK_STATUSES = FINAL_CHECK_STATUSES + PRE_RUN_CHECK_STATUSES

    # TODO: permissions @check_nperm(['read.testsuit.automatic', 'read.testsuit.manual'])
    def index(self, *args, **kwargs):
        context = DictLookup()
        context.main = 'Welcome on the contact verification page.'
        return self._render('base', ctx=context)

    def _get_contact_checks(self, test_suit=None, contact_id=None):
        log_req = create_log_request('ContactCheckFilter', references=[('contact', int(contact_id))] if contact_id else None)
        try:
            if contact_id:
                checks = cherrypy.session['Verification'].getChecksOfContact(contact_id, None, 100)
            else:
                checks = cherrypy.session['Verification'].getActiveChecks(test_suit)
            log_req.result = 'Success'
            return checks
        finally:
            log_req.close()

    @staticmethod
    def _get_to_resolve_date(check):
            if check.test_suite_handle == 'manual' and check.current_status in ('enqueue_req', 'fail_req'):
                to_resolve = check.updated
            elif check.last_test_finished:
                if check.test_suite_handle in ('manual', 'thank_you'):
                    to_resolve = check.last_test_finished + datetime.timedelta(config.verification_check_manual_waiting)
                    if check.last_contact_update > check.created:  # only updates wich happend after check was created
                        to_resolve = min(to_resolve, check.last_contact_update)
                else:
                    to_resolve = check.last_test_finished
            else:
                to_resolve = ''
            return to_resolve

    def _table_data_generator(self, test_suit=None, contact_id=None):
        checks = c2u(self._get_contact_checks(test_suit, contact_id))

        for check in checks:
            if not check_nperm_func('read.contactcheck_%s' % check.test_suite_handle):
                continue
            to_resolve = self._get_to_resolve_date(check)
            if to_resolve:
                to_resolve = to_resolve.isoformat()

            check_link = '<a href="{0}detail/{1}/"><img src="/img/icons/open.png" title="{3}" /></a>'
            if (check.current_status not in self.UNCLOSABLE_CHECK_STATUSES
                    and check_nperm_func('change.contactcheck_%s' % check.test_suite_handle)):
                cache_key = (RESOLVE_LOCK_CACHE_KEY % check.check_handle).encode('utf-8')
                resolving_user = cache.get(cache_key) if cache is not None else None
                if resolving_user and resolving_user != cherrypy.session['user'].login:
                    check_link += '&nbsp;%s resolving' % resolving_user
                else:
                    check_link += '''&nbsp;<a href="{0}detail/{1}/resolve/">{2}</a>'''
            check_link = check_link.format(f_urls[self.classname], check.check_handle, _('Resolve'), _('Show'))
            row = [
                check_link,
                '<a href="{}detail/?id={}">{}</a>'.format(f_urls['contact'], check.contact_id, check.contact_handle),
                ContactCheckEnums.SUITE_NAMES.get(check.test_suite_handle, _('!Unknown error!')),
                to_resolve,
                check.created.isoformat(),
                ContactCheckEnums.CHECK_STATUS_NAMES.get(check.current_status, _('!Unknown error!')),
            ]
            yield row

    def _generate_update_tests_form_class(self, check):
        fields = {}
        for test_data in check.test_list:
            choices = []

            choices.extend([[status, ContactCheckEnums.TEST_STATUS_NAMES[status]]
                            for status in self.SETTABLE_TEST_STATUSES])
            current_test_status = test_data.status_history[-1].status
            if current_test_status not in self.SETTABLE_TEST_STATUSES:
                choices.append([current_test_status, ContactCheckEnums.TEST_STATUS_NAMES[current_test_status]])

            fields[test_data.test_handle] = ChoiceField(test_data.test_handle, choices=choices, as_radio_buttons=True)
        return type('CheckTestsForm', (Form,), fields)

    def _get_checks_table_tag(self):
        table_tag = SimpleTable(
            header=[_('Action'), _('Contact'), _('Check type'), _('To resolve since'), _('Create date'), _('Status')],
            data=None,
            id='table_tag',
            cssc='itertable',
        )
        table_tag.media_files.extend(['/css/itertable.css',
                                      '/js/scw.js', '/js/scwLanguages.js',
                                      '/js/jquery.dataTables.js', '/js/contactcheck_list.js'])
        return table_tag

    @check_nperm(['read.contactcheck_automatic', 'read.contactcheck_manual', 'read.contactcheck_thank_you'])
    def filter(self, contact_id=None):
        context = DictLookup({
            'heading': _('Contact checks'),
            'ajax_json_filter_url': f_urls['contactcheck'] + 'json_filter/' + ('%s/' % contact_id if contact_id else ''),
            'table_tag': self._get_checks_table_tag(),
        })
        if contact_id is None:  # don't set filter when user is wating check of particular contact:
            context['default_js_type_filter'] = 'filter-manual' if check_nperm_func('change.contactcheck_manual') \
                                                                else 'filter-automatic'
        return self._render('filter', ctx=context)

    @check_nperm(['read.contactcheck_automatic', 'read.contactcheck_manual', 'read.contactcheck_thank_you'])
    def json_filter(self, contact_id=None, **kwd):
        test_suit = kwd.get('test_suit')
        if contact_id:
            try:
                contact_id = int(contact_id)
            except (TypeError, ValueError):
                context = {'main': _('Requires integer as parameter (got %s).' % contact_id)}
                raise CustomView(self._render('base', ctx=context))

        cherrypy.response.headers['Content-Type'] = 'application/json'
        data = list(self._table_data_generator(test_suit, contact_id))
        json_data = json.dumps({'aaData': data})
        return json_data

    def _get_check_messages_list(self, check):
        messages = c2u(cherrypy.session['Verification'].getContactCheckMessages(u2c(check.contact_id)))

        if len(messages):
            messages_table = SimpleTable(
                header=[_('Id'), _('Created'), _('Channel'), _('Type'), _('Updated'), _('Status')],
                data=[(a(attr(href=f_urls['mail' if msg.type_handle == 'email' else 'message'] + 'detail/?id=%s' % msg.id),
                         img(src='/img/icons/open.png')),
                       msg.created, msg.type_handle, msg.content_handle, msg.updated, msg.status)
                       for msg in messages],
                cssc='itertable'
            )
            messages_table.media_files.append('/css/itertable.css')
            return messages_table
        else:
            return _('No messages have been sent.')

    @login_required
    def detail(self, *args, **kwd):
        # path can be 'detail/ID/' or 'detail/ID/resolve/'
        if (not 1 <= len(args) <= 2) or (len(args) > 1 and args[1] != 'resolve'):
            return self._render('404_not_found')

        check_handle = args[0]
        if len(args) > 1:
            # cache lock is just helping users so they don't work on the same Check, but it's optional:
            if cache:
                cache_key = RESOLVE_LOCK_CACHE_KEY % check_handle
                stored = cache.add(cache_key,
                                   cherrypy.session['user'].login,
                                   config.verification_check_lock_default_duration)
                current_resolving_user = cache.get(cache_key)
                # resolve only if memcache is not running (return value 0) or lock was acquired (return value True) or
                # the current user is the user who has the lock:
                if (stored == 0 and type(stored) == type(0)) or stored is True \
                    or current_resolving_user == cherrypy.session['user'].login:
                    resolve = True
                else:
                    messages.warning('This check is currently being resolved by the user "%s"' % current_resolving_user)
                    raise cherrypy.HTTPRedirect(f_urls['contactcheck'] + 'detail/%s/' % check_handle)
            else:
                resolve = True
        else:  # read only mode
            resolve = False

        post_data = kwd if cherrypy.request.method == 'POST' else None

        if resolve and post_data:
            req_type = 'ContactCheckUpdateTestStatuses'
        else:
            req_type = 'ContactCheckDetail'

        log_req = create_log_request(req_type, properties=[['check_handle', check_handle]])
        out_props = []

        check = None
        try:
            check = c2u(cherrypy.session['Verification'].getContactCheckDetail(check_handle))
            if resolve:
                check_nperm_func('change.contactcheck_%s' % check.test_suite_handle, raise_err=True)
            else:
                check_nperm_func('read.contactcheck_%s' % check.test_suite_handle, raise_err=True)

            if resolve:
                if self._is_check_post_closed(check):
                    messages.warning(_('This contact check was already resolved.'))
                    raise cherrypy.HTTPRedirect(f_urls['contactcheck'] + 'detail/%s/' % check.check_handle)
                elif self._is_check_pre_run(check) and check.status_history[-1].status != 'enqueue_req':
                    messages.warning(_('This contact check was not yet run.'))
                    raise cherrypy.HTTPRedirect(f_urls['contactcheck'] + 'detail/%s/' % check.check_handle)

                initial = {test_data.test_handle: test_data.status_history[-1].status for test_data in check.test_list}
                form = self._generate_update_tests_form_class(check)(post_data, initial=initial)
                if form.is_valid():
                    changed_statuses = {}
                    for test_data in check.test_list:
                        status_in_form = form.cleaned_data[test_data.test_handle]
                        if status_in_form != test_data.status_history[-1].status:
                            changed_statuses[test_data.test_handle] = status_in_form
                    if changed_statuses:
                        cherrypy.session['Verification'].updateContactCheckTests(
                            u2c(check.check_handle),
                            u2c([Registry.AdminContactVerification.ContactTestUpdate(test_handle, status)
                                 for test_handle, status in changed_statuses.items()]),
                            u2c(log_req.request_id))
                    log_req.result = 'Success'
                    out_props += [['changed_statuses', '']] + [[key, val, True] for key, val in changed_statuses.items()]
                    self._update_check(check, post_data)
                else:
                    log_req.result = 'Fail'
            else:
                form = None

            log_req.result = 'Success'

            detail = VerificationCheckDetail(
                check=check,
                resolve=resolve,
                form=form
            )

            try:
                contact_detail = get_detail('contact', check.contact_id)
            except ccReg.Admin.ObjectNotFound:
                contact_detail = None

            context = DictLookup({
                'test_suit_name': ContactCheckEnums.SUITE_NAMES.get(check.test_suite_handle),
                'check': check,
                'contact_url': f_urls['contact'] + 'detail/?id=%s' % check.contact_id,
                'detail': detail,
                'contact_detail': contact_detail,
                'ajax_json_filter_url': f_urls['contactcheck'] + 'json_filter/%s/' % check.contact_id,
            })
            if cherrypy.session.get('history', False):
                context.update({
                    'table_tag': self._get_checks_table_tag(),
                    'messages_list': self._get_check_messages_list(check)
                })
            return self._render('detail', ctx=context)
        except Registry.AdminContactVerification.INVALID_CHECK_HANDLE:
            log_req.result = 'Fail'
            return self._render('404_not_found')
        finally:
            log_req.close(properties=out_props, references=[('contact', check.contact_id)] if check else None)

    def _update_check(self, check, post_data):
        status_action = post_data['status_action']
        if status_action not in get_status_action(check.test_suite_handle, check.status_history[-1].status):
            raise CustomView(self._render('error',
                                          ctx={'message': _('Unknown status_action "%s" to resolve.' % status_action)}))
        status, action = status_action.split(':')

        props = [['check_handle', check.check_handle],
                 ['status', status],
                 ['action', action]]
        log_req = create_log_request('ContactCheckResolve', properties=props,
                                      references=[('contact', check.contact_id)])
        try:
            if status == 'confirm_enqueue':
                cherrypy.session['Verification'].confirmEnqueueingContactCheck(u2c(check.check_handle),
                                                                               log_req.request_id)
                messages.success(_('Contact check has been enqueue.'))
            else:
                cherrypy.session['Verification'].resolveContactCheckStatus(u2c(check.check_handle),
                                                                           u2c(status), log_req.request_id)
                messages.success(_('Contact check has been resolved as {}.').format(
                    ContactCheckEnums.CHECK_STATUS_NAMES[status]))

            if action == 'add_manual':
                self._create_check(check.contact_id, 'manual', redirect_to_contact=False)
            elif action == 'add_thank_you':
                self._create_check(check.contact_id, 'thank_you', redirect_to_contact=False)
            elif action == 'delete_domains':
                cherrypy.session['Verification'].deleteDomainsAfterFailedManualCheck(u2c(check.check_handle))
                messages.success(_('All domains held by the contact {} were deleted.').format(check.contact_handle))

            log_req.result = 'Success'

            raise cherrypy.HTTPRedirect(f_urls['contactcheck'] + 'detail/%s/' % check.check_handle)
        finally:
            log_req.close()

    def _template(self, action=''):
        if action == 'filter':
            return ContactCheckList
        elif action == 'detail':
            return ContactCheckDetail
        else:
            return super(ContactCheck, self)._template(action=action)

    def _get_menu_handle(self, action):
        return 'contactcheck'

    @classmethod
    def _is_check_pre_run(self, check):
        return check.status_history[-1].status in self.PRE_RUN_CHECK_STATUSES

    def _is_check_post_closed(self, check):
        return check.status_history[-1].status in self.FINAL_CHECK_STATUSES

    def _create_check(self, contact_id, test_suite_handle, redirect_to_contact=True):
        check_nperm_func('add.contactcheck_%s' % test_suite_handle, raise_err=True)
        try:
            contact_id = int(contact_id)
        except (TypeError, ValueError):
            context = {'main': _('Requires integer as parameter (got %s).' % contact_id)}
            raise CustomView(self._render('base', ctx=context))

        log_req = create_log_request('ContactCheckEnqueue', properties=[['test_suit_handle', test_suite_handle]],
                                     references=[('contact', int(contact_id))])
        try:
            cherrypy.session['Verification'].enqueueContactCheck(contact_id, test_suite_handle, log_req.request_id)
            log_req.result = 'Success'
            messages.success(_('New %s contact check has been created.' % test_suite_handle))
            if redirect_to_contact:
                raise cherrypy.HTTPRedirect(f_urls['contact'] + 'detail/?id=%s' % contact_id)
        finally:
            log_req.close()

    def create_check(self, contact_id, test_suite_handle, **kwd):
        return self._create_check(contact_id, test_suite_handle)
