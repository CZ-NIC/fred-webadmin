import datetime
import json

import cherrypy

from .base import AdifPage
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


class ContactCheck(AdifPage):
    SETTABLE_TEST_STATUSES = ('ok', 'fail')
    OK_TEST_STATUSES = ('ok', 'skipped')
    FAIL_TEST_STATUSES = ('fail', 'skipped')
    FINAL_CHECK_STATUSES = ('ok', 'fail', 'invalidated')
    UNCLOSABLE_CHECK_STATUSES = FINAL_CHECK_STATUSES + ('enqueued', 'running')

    # TODO: permissions @check_nperm(['read.testsuit.automatic', 'read.testsuit.manual'])
    def index(self, *args, **kwargs):
        context = DictLookup()
        context.main = 'Welcome on the contact verification page.'
        return self._render('base', ctx=context)

    def _get_contact_checks(self, test_suit=None, contact_id=None):
        log_req = create_log_request('ContactCheckFilter')
        try:
            checks = cherrypy.session['Verification'].getActiveChecks(test_suit)
            log_req.result = 'Success'
            return checks
        finally:
            log_req.close()

    def _table_data_generator(self, test_suit=None, contact_id=None):
        checks = self._get_contact_checks(test_suit, contact_id)

        for check in checks:
            test_finished_python = c2u(check.last_test_finished)
            if test_finished_python:
                if check.test_suite_handle == 'manual':
                    last_contact_update = c2u(check.last_contact_update)
                    to_resolve = min(test_finished_python + datetime.timedelta(30),  # TODO: put into config
                                     last_contact_update)
                else:
                    to_resolve = test_finished_python
                to_resolve = to_resolve.isoformat()
            else:
                to_resolve = ''

            check_link = '<a href="{0}detail/{1}/"><img src="/img/icons/open.png" title="{3}" /></a>'
            if check.current_status not in self.UNCLOSABLE_CHECK_STATUSES:
                check_link += '''<a href="{0}detail/{1}/resolve/">{2}</a>'''
            check_link = check_link.format(f_urls[self.classname], c2u(check.check_handle), _('Resolve'), _('Show'))
            row = [
                check_link,
                '<a href="{}detail/?id={}">{}</a>'.format(f_urls['contact'], c2u(check.contact_id), c2u(check.contact_handle)),
                ContactCheckEnums.SUITE_NAMES.get(c2u(check.test_suite_handle), _('!Unknown error!')),
                to_resolve,
                c2u(check.created).isoformat(),
                ContactCheckEnums.CHECK_STATUS_NAMES.get(c2u(check.current_status), _('!Unknown error!')),
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
    def json_filter(self, **kwd):
        test_suit = kwd.get('test_suit')
        try:
            if kwd.get('contact_id'):
                contact_id = int(kwd.get('contact_id'))
            else:
                contact_id = None
        except (TypeError, ValueError):
            context = {'main': _('Requires integer as parameter (got %s).' % kwd['contact_id'])}
            raise CustomView(self._render('base', ctx=context))

        cherrypy.response.headers['Content-Type'] = 'application/json'
        data = list(self._table_data_generator(test_suit, contact_id))
        json_data = json.dumps({'aaData': data})
        return json_data

    @login_required
    def detail(self, *args, **kwd):
        # path can be 'detail/ID/' or 'detail/ID/resolve/'
        if ((not 1 <= len(args) <= 3) or
                (len(args) > 1 and args[1] != 'resolve') or
                (len(args) == 3 and cherrypy.request.method != 'POST')):
            return self._render('404_not_found')

        check_handle = args[0]
        if len(args) > 1:  # can resolve the check
            resolve = True
        else:  # read only mode
            resolve = False

        if len(args) == 3:
            self._close_check(check_handle, args[2])  # closing check ends with redirection

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
                if not self.is_check_closable(check):
                    messages.warning(_('This contact check was already resolved.'))
                    raise cherrypy.HTTPRedirect(f_urls['contactcheck'] + 'detail/%s/' % check.check_handle)

                form = self._generate_update_tests_form_class(check)(
                    post_data,
                    submit_button_text=_('Save'))
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
                    messages.success(_('Changes have been saved.'))
                    raise cherrypy.HTTPRedirect('resolve/')
            else:
                form = None

            log_req.result = 'Success'

            detail = VerificationCheckDetail(
                check=check,
                resolve=resolve,
                form=form
            )

            if resolve and self.is_check_closable(check):
                filters = [[]]

                # Tests statuses must be either all OK or all fail to be possible to resolve check as OK or fail.
                # Tests wish status 'skipped' are irrelevant and ignored in these conditions:
                if all([test.status_history[-1].status in self.OK_TEST_STATUSES for test in check.test_list]):
                    filters[0].append([Form(action='ok/', method='post', submit_button_text=_('Resolve as OK'),
                                            onsubmit='return confirm("Are you sure?")')])
                if all([test.status_history[-1].status in self.FAIL_TEST_STATUSES for test in check.test_list]):
                    filters[0].append([Form(action='fail/', method='post', submit_button_text=_('Resolve as failed'),
                                            onsubmit='return confirm("Are you sure?")')])

                filters[0].append([Form(action='invalidated/', method='post', submit_button_text=_('Invalidate'),
                                            onsubmit='return confirm("Are you sure?")')])

                panel = FilterPanel(filters)
                panel.media_files.append('/js/public_profile.js')
            else:
                panel = None

            context = DictLookup({
                'test_suit_name': ContactCheckEnums.SUITE_NAMES.get(check.test_suite_handle),
                'check': check,
                'contact_url': f_urls['contact'] + 'detail/?id=%s' % check.contact_id,
                'detail': detail,
                'panel': panel,
            })
            return self._render('detail', ctx=context)
        finally:
            log_req.close()

    def _close_check(self, check_handle, close_status):
        log_req = create_log_request('ContactCheckDetail', properties=[['check_handle', check_handle]])
        try:
            cherrypy.session['Verification'].resolveContactCheckStatus(check_handle, close_status, log_req.request_id)
            log_req.result = 'Success'
            messages.success(_('Contact check has been resolved as {}.').format(
                               ContactCheckEnums.CHECK_STATUS_NAMES[close_status]))
            raise cherrypy.HTTPRedirect('../')
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
    def is_check_closable(self, check):
        return check.status_history[-1].status not in self.UNCLOSABLE_CHECK_STATUSES
