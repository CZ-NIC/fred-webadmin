import datetime
import json

import cherrypy

from .base import AdifPage
from fred_webadmin.cache import cache
from fred_webadmin import config
from fred_webadmin.controller.perms import check_nperm, login_required
from fred_webadmin.corba import Registry
from fred_webadmin.corbarecoder import c2u, u2c
from fred_webadmin.customview import CustomView
from fred_webadmin.enums import ContactCheckEnums
from fred_webadmin.mappings import f_urls
from fred_webadmin import messages
from fred_webadmin.translation import _
from fred_webadmin.utils import create_log_request
from fred_webadmin.webwidgets.details.administrative_verification import VerificationCheckDetail
from fred_webadmin.webwidgets.forms.forms import Form
from fred_webadmin.webwidgets.forms.fields import ChoiceField
from fred_webadmin.webwidgets.gpyweb.gpyweb import DictLookup
from fred_webadmin.webwidgets.simple_table import SimpleTable
from fred_webadmin.webwidgets.templates.pages import ContactCheckList, ContactCheckDetail
from fred_webadmin.webwidgets.adifwidgets import FilterPanel

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
        log_req = create_log_request('ContactCheckFilter')
        try:
            if contact_id:
                checks = cherrypy.session['Verification'].getChecksOfContact(contact_id, None, 100)
            else:
                checks = cherrypy.session['Verification'].getActiveChecks(test_suit)
            log_req.result = 'Success'
            return checks
        finally:
            log_req.close()

    def _table_data_generator(self, test_suit=None, contact_id=None):
        checks = c2u(self._get_contact_checks(test_suit, contact_id))

        for check in checks:
            if check.last_test_finished:
                if check.test_suite_handle == 'manual':
                    to_resolve = check.last_test_finished + datetime.timedelta(config.verification_check_manual_waiting)
                    if check.last_contact_update > check.created:  # only updates wich happend after check was created
                        to_resolve = min(to_resolve, check.last_contact_update)
                else:
                    to_resolve = check.last_test_finished
                to_resolve = to_resolve.isoformat()
            else:
                to_resolve = ''

            check_link = '<a href="{0}detail/{1}/"><img src="/img/icons/open.png" title="{3}" /></a>'
            if check.current_status not in self.UNCLOSABLE_CHECK_STATUSES:
                cache_key = (RESOLVE_LOCK_CACHE_KEY % check.check_handle).encode('utf-8')
                resolving_user = cache.get(cache_key)
                if resolving_user and resolving_user != cherrypy.session['user'].login:
                    check_link += '%s resolving' % resolving_user
                else:
                    check_link += '''<a href="{0}detail/{1}/resolve/">{2}</a>'''
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
        choices = [['no_change', _('No change')]]
        choices.extend([[status, ContactCheckEnums.CHECK_STATUS_NAMES[status]]
                        for status in self.SETTABLE_TEST_STATUSES])
        fields = {}
        for test_data in check.test_list:
            fields[test_data.test_handle] = ChoiceField(test_data.test_handle, choices=choices)
        return type('CheckTestsForm', (Form,), fields)

    @login_required
    def filter(self, contact_id=None):
        table_tag = SimpleTable(
                     header=[_('Action'), _('Contact'), _('Check type'), _('To resolve since'), _('Create date'), _('Status')],
                     data=None,
                     id='table_tag',
                     cssc='itertable',
                 )
        table_tag.media_files.extend(['/css/itertable.css',
                                      '/js/scw.js', '/js/scwLanguages.js',
                                      '/js/jquery.dataTables.js', '/js/contactcheck_list.js'])
        context = DictLookup({
            'heading': _('Contact checks'),
            'table_tag': table_tag,
        })
        return self._render('filter', ctx=context)

    @login_required
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

    @login_required
    def detail(self, *args, **kwd):
        # path can be 'detail/ID/' or 'detail/ID/resolve/'
        if (not 1 <= len(args) <= 2) or (len(args) > 1 and args[1] != 'resolve'):
            return self._render('404_not_found')

        check_handle = args[0]
        if len(args) > 1:
            cache_key = RESOLVE_LOCK_CACHE_KEY % check_handle
            stored = cache.add(cache_key,
                               cherrypy.session['user'].login,
                               config.verification_check_lock_default_duration)
            current_resolving_user = cache.get(cache_key)
            if stored or current_resolving_user == cherrypy.session['user'].login:
                resolve = True
            else:
                messages.warning('This check is currently being resolved by user "%s"' % current_resolving_user)
                raise cherrypy.HTTPRedirect(f_urls['contactcheck'] + 'detail/%s/' % check_handle)
        else:  # read only mode
            resolve = False

        post_data = kwd if cherrypy.request.method == 'POST' else None

        if resolve and post_data:
            req_type = 'ContactCheckUpdateTestStatuses'
        else:
            req_type = 'ContactCheckDetail'
        props = [['check_handle', check_handle]]
        log_req = create_log_request(req_type, props)

        try:
            check = c2u(cherrypy.session['Verification'].getContactCheckDetail(check_handle))

            if resolve:
                if self._is_check_post_closed(check):
                    messages.warning(_('This contact check was already resolved.'))
                    raise cherrypy.HTTPRedirect(f_urls['contactcheck'] + 'detail/%s/' % check.check_handle)
                elif self._is_check_pre_run(check):
                    messages.warning(_('This contact check was not yet run.'))
                    raise cherrypy.HTTPRedirect(f_urls['contactcheck'] + 'detail/%s/' % check.check_handle)

                form = self._generate_update_tests_form_class(check)(post_data)
                if form.is_valid():
                    changed_statuses = {}
                    for test_handle, field_value in form.cleaned_data.items():
                        if field_value != 'no_change':
                            changed_statuses[test_handle] = field_value
                    cherrypy.session['Verification'].updateContactCheckTests(
                        u2c(check.check_handle),
                        u2c([Registry.AdminContactVerification.ContactTestUpdate(test_handle, status)
                             for test_handle, status in changed_statuses.items()]),
                        u2c(log_req.request_id))
                    if 'submit_fail' in post_data:
                        status = 'fail'
                    elif 'submit_invalidate' in post_data:
                        status = 'invalidated'
                    elif 'submit_ok' in post_data:
                        status = 'ok'
                    else:
                        raise CustomView(self._render('error', ctx={'message': _('Unknown status to resolve.')}))

                    self._close_check(check_handle, status)  # closing check ends with redirection
            else:
                form = None

            log_req.result = 'Success'

            detail = VerificationCheckDetail(
                check=check,
                resolve=resolve,
                form=form
            )


            context = DictLookup({
                'test_suit_name': ContactCheckEnums.SUITE_NAMES.get(check.test_suite_handle),
                'check': check,
                'contact_url': f_urls['contact'] + 'detail/?id=%s' % check.contact_id,
                'detail': detail,
            })
            return self._render('detail', ctx=context)
        finally:
            log_req.close()

    def _close_check(self, check_handle, close_status):
        log_req = create_log_request('ContactCheckResolve', properties=[['check_handle', check_handle]])
        try:
            cherrypy.session['Verification'].resolveContactCheckStatus(check_handle, close_status, log_req.request_id)
            log_req.result = 'Success'
            messages.success(_('Contact check has been resolved as {}.').format(
                               ContactCheckEnums.CHECK_STATUS_NAMES[close_status]))
            raise cherrypy.HTTPRedirect(f_urls['contactcheck'] + 'detail/%s/' % check_handle)
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

    def create_check(self, contact_id, test_suite_handle, **kwd):
        try:
            contact_id = int(contact_id)
        except (TypeError, ValueError):
            context = {'main': _('Requires integer as parameter (got %s).' % contact_id)}
            raise CustomView(self._render('base', ctx=context))

        log_req = create_log_request('ContactCheckEnqueue', properties=[['test_suit_handle', test_suite_handle]])
        try:
            cherrypy.session['Verification'].enqueueContactCheck(contact_id, test_suite_handle, log_req.request_id)
            log_req.result = 'Success'
            messages.success(_('Contact check have been created.'))
            raise cherrypy.HTTPRedirect(f_urls['contact'] + 'detail/?id=%s' % contact_id)
        finally:
            log_req.close()
