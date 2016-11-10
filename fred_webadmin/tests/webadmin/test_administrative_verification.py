from datetime import datetime
import json

import mock
import twill.commands as tc

from fred_webadmin import config
from fred_webadmin.controller.administrative_verification import ContactCheck
from fred_webadmin.corba import Registry, ccReg
from fred_webadmin.tests.webadmin.base import init_test_server, deinit_test_server, enable_corba_comparison_decorator, \
    TestAuthorizer
from fred_webadmin.tests.webadmin.test_adif import BaseADIFTestCase
from nose.tools import assert_equal, assert_equals
from fred_webadmin.tests.webadmin.corba_detail_maker import CorbaDetailMaker


def setup_module():
    init_test_server()


def teardown_module():
    deinit_test_server()


class TestContactVerificationBase(BaseADIFTestCase):
    def setUp(self):
        super(TestContactVerificationBase, self).setUp()
        self.admin_mock.createSession('testuser')
        self.session_mock = self.admin_mock.getSession('testSessionString')
        self.verif_mock = mock.Mock(Registry.AdminContactVerification._objref_Server)  # pylint: disable=W0212
        self.verif_mock.listCheckStatusDefs.return_value = [
            Registry.AdminContactVerification.ContactCheckStatusDef(handle='enqueue_req', name='enqueue_req', description='Request to create check.'),
            Registry.AdminContactVerification.ContactCheckStatusDef(handle='enqueued', name='enqueued', description='Check is created.'),
            Registry.AdminContactVerification.ContactCheckStatusDef(handle='running', name='running', description="Tests contained in this check haven't finished yet."),
            Registry.AdminContactVerification.ContactCheckStatusDef(handle='auto_to_be_decided', name='auto_to_be_decided', description='Automatic tests evaluation gave no result.'),
            Registry.AdminContactVerification.ContactCheckStatusDef(handle='auto_ok', name='auto_ok', description='Automatic tests evaluation proposes status ok.'),
            Registry.AdminContactVerification.ContactCheckStatusDef(handle='auto_fail', name='auto_fail', description='Automatic tests evaluation proposes status fail. '),
            Registry.AdminContactVerification.ContactCheckStatusDef(handle='ok', name='ok', description='Data were manually evaluated as valid.'),
            Registry.AdminContactVerification.ContactCheckStatusDef(handle='fail_req', name='fail_req', description='Data are probably invalid, needs confirmation.'),
            Registry.AdminContactVerification.ContactCheckStatusDef(handle='fail', name='fail', description='Data were manually evaluated as invalid.'),
            Registry.AdminContactVerification.ContactCheckStatusDef(handle='invalidated', name='invalidated', description='Check was manually set to be ignored.')
        ]
        self.verif_mock.listTestSuiteDefs.return_value = [
            Registry.AdminContactVerification.ContactTestSuiteDef(handle='automatic', name='automatic', description='Tests without any contact owner cooperation.',
                                                                  tests=[Registry.AdminContactVerification.ContactTestDef(handle='name_syntax', name='name_syntax', description='Testing syntactical validity of name'),
                                                                         Registry.AdminContactVerification.ContactTestDef(handle='phone_syntax', name='phone_syntax', description='Testing syntactical validity of phone'),
                                                                         Registry.AdminContactVerification.ContactTestDef(handle='email_syntax', name='email_syntax', description='Testing syntactical validity of e-mail'),
                                                                         Registry.AdminContactVerification.ContactTestDef(handle='cz_address_existence', name='cz_address_existence', description='Testing address against official dataset (CZ only)'),
                                                                         Registry.AdminContactVerification.ContactTestDef(handle='email_host_existence', name='email_host_existence', description='Testing if e-mail host exists')]),
            Registry.AdminContactVerification.ContactTestSuiteDef(handle='manual', name='manual', description='Tests where contact owner is actively taking part or is being informed.',
                                                                  tests=[Registry.AdminContactVerification.ContactTestDef(handle='contactability', name='contactability', description='Testing if contact is reachable by e-mail or letter')]),
            Registry.AdminContactVerification.ContactTestSuiteDef(handle='thank_you', name='thank_you', description='"Thank you" letter used for contactability testing',
                                                                  tests=[Registry.AdminContactVerification.ContactTestDef(handle='send_letter', name='send_letter', description='Testing if contact is reachable by letter')])
        ]
        self.verif_mock.listTestStatusDefs.return_value = [
            Registry.AdminContactVerification.ContactTestStatusDef(handle='enqueued', name='enqueued', description='Test is ready to be run.'),
            Registry.AdminContactVerification.ContactTestStatusDef(handle='running', name='running', description='Test is running.'),
            Registry.AdminContactVerification.ContactTestStatusDef(handle='skipped', name='skipped', description='Test run was intentionally skipped.'),
            Registry.AdminContactVerification.ContactTestStatusDef(handle='error', name='error', description='Error happened during test run.'),
            Registry.AdminContactVerification.ContactTestStatusDef(handle='manual', name='manual', description='Result is inconclusive and evaluation by human is needed.'),
            Registry.AdminContactVerification.ContactTestStatusDef(handle='ok', name='ok', description='Test result is OK.'),
            Registry.AdminContactVerification.ContactTestStatusDef(handle='fail', name='fail', description='Test result is FAIL.')
        ]
        self.verif_mock.listTestDefs.return_value = [
                Registry.AdminContactVerification.ContactTestDef(handle='name_syntax', name='name_syntax', description='Testing syntactical validity of name'),
                Registry.AdminContactVerification.ContactTestDef(handle='phone_syntax', name='phone_syntax', description='Testing syntactical validity of phone'),
                Registry.AdminContactVerification.ContactTestDef(handle='email_syntax', name='email_syntax', description='Testing syntactical validity of e-mail'),
                Registry.AdminContactVerification.ContactTestDef(handle='cz_address_existence', name='cz_address_existence', description='Testing address against official dataset (CZ only)'),
                Registry.AdminContactVerification.ContactTestDef(handle='email_host_existence', name='email_host_existence', description='Testing if e-mail host exists'),
                Registry.AdminContactVerification.ContactTestDef(handle='contactability', name='contactability', description='Testing if contact is reachable by e-mail or letter'),
                Registry.AdminContactVerification.ContactTestDef(handle='send_letter', name='send_letter', description='Testing if contact is reachable by letter'),
        ]
        self.web_session_mock['Verification'] = self.verif_mock

    def _check_li(self, handle='a', test_suite_handle='automatic',
                  contact_id=1L, contact_handle='KONTAKT',
                  created=datetime(2014, 1, 1, 13, 30, 45), updated=datetime(2014, 1, 2, 9, 55, 47),
                  last_test_finished=datetime(2014, 1, 2, 9, 55, 47),
                  last_contact_update=datetime(2013, 12, 22, 12, 34, 56),
                  current_status='auto_fail'):
        '''Creates check list item'''
        return Registry.AdminContactVerification.ContactCheckListItem(
            check_handle=handle, test_suite_handle=test_suite_handle,
            contact_id=contact_id, contact_handle=contact_handle,
            contact_hid=1L, checked_contact_hid=1L,
            created=ccReg.DateTimeType(date=ccReg.DateType(day=created.day, month=created.month, year=created.year), hour=created.hour, minute=created.minute, second=created.second),
            updated=ccReg.DateTimeType(date=ccReg.DateType(day=updated.day, month=updated.month, year=updated.year), hour=updated.hour, minute=updated.minute, second=updated.second),
            last_test_finished=ccReg.DateTimeType(date=ccReg.DateType(day=last_test_finished.day, month=last_test_finished.month, year=last_test_finished.year), hour=last_test_finished.hour, minute=last_test_finished.minute, second=last_test_finished.second),
            last_contact_update=ccReg.DateTimeType(date=ccReg.DateType(day=last_contact_update.day, month=last_contact_update.month, year=last_contact_update.year), hour=last_contact_update.hour, minute=last_contact_update.minute, second=last_contact_update.second),
            current_status='auto_fail')


class TestCheckList(TestContactVerificationBase):
    def test_list_page(self):
        tc.go('http://localhost:8080/contactcheck/filter/')
        tc.find('Contact checks')

    def test_json_filter_all(self):
        self.verif_mock.getActiveChecks.return_value = [
            Registry.AdminContactVerification.ContactCheckListItem(check_handle='a', test_suite_handle='automatic', contact_id=75L, contact_handle='KONTAKT', checked_contact_hid=1L, created=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=16, minute=13, second=14), updated=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=16, minute=13, second=32), last_test_finished=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=14, minute=13, second=14), last_contact_update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=14, minute=13, second=0), current_status='auto_fail'), ]
        tc.go('http://localhost:8080/contactcheck/json_filter/')
        data = json.loads(tc.browser.result.text)
        assert_equal(data['aaData'][0][2], 'automatic')

    def test_json_filter_contact_id(self):
        self.verif_mock.getChecksOfContact.return_value = [
            Registry.AdminContactVerification.ContactCheckListItem(check_handle='a', test_suite_handle='manual', contact_id=75L, contact_handle='KONTAKT', checked_contact_hid=1L, created=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=16, minute=13, second=14), updated=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=16, minute=13, second=32), last_test_finished=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=14, minute=13, second=14), last_contact_update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=14, minute=13, second=0), current_status='enqueued'), ]
        tc.go('http://localhost:8080/contactcheck/json_filter/75/')
        data = json.loads(tc.browser.result.text)
        assert_equal(data['aaData'][0][2], 'manual')

    def test_to_resolve_since_date_automatic(self):
        check = mock.Mock(test_suite_handle='automatic',
                          current_status='enqueue',
                          created=datetime(2014, 1, 1),
                          last_test_finished=None)
        assert_equals(ContactCheck._get_to_resolve_date(check), '')

        check.current_status = 'auto_fail'
        check.last_test_finished = datetime(2014, 1, 2)
        assert_equals(ContactCheck._get_to_resolve_date(check), datetime(2014, 1, 2))

    def test_to_resolve_since_date_manual(self):
        self.monkey_patch(config, 'verification_check_manual_waiting', 30)
        check = mock.Mock(test_suite_handle='manual',
                          current_status='enqueue_req',
                          created=datetime(2014, 1, 1),
                          updated=datetime(2014, 1, 2),
                          last_contact_update=datetime(2013, 06, 12),
                          last_test_finished=None)
        assert_equals(ContactCheck._get_to_resolve_date(check), datetime(2014, 1, 2))  # same as updated

        check.current_status = 'enqueued'
        assert_equals(ContactCheck._get_to_resolve_date(check), '')

        check.current_status = 'auto_to_be_decided'
        check.last_test_finished = datetime(2014, 1, 3)
        assert_equals(ContactCheck._get_to_resolve_date(check), datetime(2014, 2, 2))  # last_contact_update + wait 30

        check.last_contact_update = datetime(2014, 1, 5)
        assert_equals(ContactCheck._get_to_resolve_date(check), datetime(2014, 1, 5))  # same as last_contact_update

        check.current_status = 'fail_req'
        check.updated = datetime(2014, 1, 6)
        assert_equals(ContactCheck._get_to_resolve_date(check), datetime(2014, 1, 6))  # same as updated

    def test_to_resolve_since_date_thank_you(self):
        self.monkey_patch(config, 'verification_check_manual_waiting', 30)
        check = mock.Mock(test_suite_handle='thank_you',
                          current_status='enqueue',
                          created=datetime(2014, 1, 1),
                          updated=datetime(2014, 1, 2),
                          last_contact_update=datetime(2013, 06, 12),
                          last_test_finished=None)
        assert_equals(ContactCheck._get_to_resolve_date(check), '')

        check.status = 'auto_to_be_decided'
        check.last_test_finished = datetime(2014, 1, 3)
        assert_equals(ContactCheck._get_to_resolve_date(check), datetime(2014, 2, 2))  # last_contact_update + wait 30

    def test_json_filter_perms(self):
        authorizer = TestAuthorizer()
        self.monkey_patch(self.web_session_mock['user'], '_authorizer', authorizer)

        self.verif_mock.getActiveChecks.side_effect = lambda test_suite: [
            Registry.AdminContactVerification.ContactCheckListItem(check_handle='a', test_suite_handle='automatic', contact_id=75L, contact_handle='KONTAKT', checked_contact_hid=1L, created=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=16, minute=13, second=14), updated=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=16, minute=13, second=32), last_test_finished=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=14, minute=13, second=14), last_contact_update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=14, minute=13, second=0), current_status='auto_fail'),
            Registry.AdminContactVerification.ContactCheckListItem(check_handle='a', test_suite_handle='manual', contact_id=75L, contact_handle='KONTAKT', checked_contact_hid=1L, created=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=16, minute=13, second=14), updated=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=16, minute=13, second=32), last_test_finished=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=14, minute=13, second=14), last_contact_update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=14, minute=13, second=0), current_status='auto_to_be_decided'),
            Registry.AdminContactVerification.ContactCheckListItem(check_handle='a', test_suite_handle='thank_you', contact_id=75L, contact_handle='KONTAKT', checked_contact_hid=1L, created=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=16, minute=13, second=14), updated=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=16, minute=13, second=32), last_test_finished=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=14, minute=13, second=14), last_contact_update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=14, minute=13, second=0), current_status='auto_to_be_decided'),
        ]

        tc.go('http://localhost:8080/contactcheck/json_filter/')
        tc.find('don\'t have permissions')

        authorizer.add_perms('read.contactcheck_automatic')
        tc.go('http://localhost:8080/contactcheck/json_filter/')
        tc.notfind('don\'t have permissions')
        data = json.loads(tc.browser.result.text)
        assert_equal(data['aaData'][0][2], 'automatic')

        authorizer.rem_perms('read.contactcheck_automatic')
        authorizer.add_perms('read.contactcheck_manual')
        tc.go('http://localhost:8080/contactcheck/json_filter/')
        tc.notfind('Resolve')
        data = json.loads(tc.browser.result.text)
        assert_equal(len(data), 1)
        assert_equal(data['aaData'][0][2], 'manual')

        authorizer.add_perms('change.contactcheck_manual')
        tc.go('http://localhost:8080/contactcheck/json_filter/')
        tc.find('Resolve')


class TestCheckDetailBase(TestContactVerificationBase):
    def _get_contact_check_func(self, test_suite_handle, check_status=None):
        ''' Returns function used for for side_effect the will return contact check of givet `test_suite`. '''
        if check_status is not None:
            current_status = check_status
        else:
            if test_suite_handle == 'automatic':
                current_status = 'auto_fail'
            else:
                current_status = 'auto_to_be_decided'
        return lambda handle: Registry.AdminContactVerification.ContactCheckDetail(
            check_handle=self.check_handle, test_suite_handle=test_suite_handle,
            contact_id=1L, contact_handle='KONTAKT', checked_contact_hid=1L,
            created=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=34, second=55),
            status_history=[Registry.AdminContactVerification.ContactCheckStatus(status='enqueue_req', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=34, second=55), logd_request_id=None),
                            Registry.AdminContactVerification.ContactCheckStatus(status='enqueued', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=34, second=55), logd_request_id=None),
                            Registry.AdminContactVerification.ContactCheckStatus(status='running', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=18), logd_request_id=None),
                            Registry.AdminContactVerification.ContactCheckStatus(status=current_status, update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=21), logd_request_id=None)],
            test_list=[Registry.AdminContactVerification.ContactTest(test_handle='name_syntax', created=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=18),
                           status_history=[Registry.AdminContactVerification.ContactTestStatus(status='enqueued', err_msg='', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=18), logd_request_id=None),
                                           Registry.AdminContactVerification.ContactTestStatus(status='running', err_msg='', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=18), logd_request_id=None),
                                           Registry.AdminContactVerification.ContactTestStatus(status='ok', err_msg='', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=18), logd_request_id=None)], tested_contact_data=['Jan Novak'], current_contact_data=['Jan Novak']),
                       Registry.AdminContactVerification.ContactTest(test_handle='phone_syntax', created=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=18),
                           status_history=[Registry.AdminContactVerification.ContactTestStatus(status='enqueued', err_msg='', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=18), logd_request_id=None),
                                           Registry.AdminContactVerification.ContactTestStatus(status='running', err_msg='', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=18), logd_request_id=None),
                                           Registry.AdminContactVerification.ContactTestStatus(status='ok', err_msg='', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=19), logd_request_id=None)], tested_contact_data=['+420.775897897'], current_contact_data=['+420.775897897']),
                       Registry.AdminContactVerification.ContactTest(test_handle='email_syntax', created=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=18),
                           status_history=[Registry.AdminContactVerification.ContactTestStatus(status='enqueued', err_msg='', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=18), logd_request_id=None),
                                           Registry.AdminContactVerification.ContactTestStatus(status='running', err_msg='', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=19), logd_request_id=None),
                                           Registry.AdminContactVerification.ContactTestStatus(status='ok', err_msg='', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=19), logd_request_id=None)], tested_contact_data=['info@mymail.cz'], current_contact_data=['info@mymail.cz']),
                       Registry.AdminContactVerification.ContactTest(test_handle='cz_address_existence', created=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=18),
                           status_history=[Registry.AdminContactVerification.ContactTestStatus(status='enqueued', err_msg='', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=18), logd_request_id=None),
                                           Registry.AdminContactVerification.ContactTestStatus(status='running', err_msg='', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=19), logd_request_id=None),
                                           Registry.AdminContactVerification.ContactTestStatus(status='fail', err_msg='', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=19), logd_request_id=None)],
                                                                                               tested_contact_data=['Namesti republiky 1230/12', 'Praha', '12000', 'CZ'],
                                                                                               current_contact_data=['Namesti generala Fejlureho 1/1', 'Praha', '13000', 'CZ']),
                       Registry.AdminContactVerification.ContactTest(test_handle='email_host_existence', created=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=18),
                           status_history=[Registry.AdminContactVerification.ContactTestStatus(status='enqueued', err_msg='', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=18), logd_request_id=None),
                                           Registry.AdminContactVerification.ContactTestStatus(status='running', err_msg='', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=21), logd_request_id=None),
                                           Registry.AdminContactVerification.ContactTestStatus(status='ok', err_msg='', update=ccReg.DateTimeType(date=ccReg.DateType(day=6, month=6, year=2014), hour=15, minute=35, second=21), logd_request_id=None)], tested_contact_data=['info@mymail.cz'], current_contact_data=['info@mymail.cz'])])

    def setUp(self):
        super(TestCheckDetailBase, self).setUp()
        self.check_handle = 'f693969f-12b4-46d5-8b3f-267a842ab3a3'
        self.verif_mock.getContactCheckDetail.side_effect = self._get_contact_check_func('automatic')
        self.session_mock.getDetail.side_effect = lambda obj_type, obj_id: CorbaDetailMaker().contact('KONTAKT')


class TestCheckDetail(TestCheckDetailBase):
    def test_detail_page(self):
        tc.go('http://localhost:8080/contactcheck/detail/%s/' % self.check_handle)
        tc.find('KONTAKT')
        tc.notfind('running')

        # check that both current contact data and tested contact data are displayed:
        tc.find('Namesti republiky')
        tc.find('Namesti generala Fejlureho')

    def test_detail_page_deleted_contact(self):
        self.session_mock.getDetail.side_effect = ccReg.Admin.ObjectNotFound
        tc.go('http://localhost:8080/contactcheck/detail/%s/' % self.check_handle)
        tc.find('Contact was deleted')

    def test_detail_page_history(self):
        self.web_session_mock['history'] = True
        self.verif_mock.getContactCheckMessages.return_value = [
            Registry.AdminContactVerification.Message(id=2L, type_handle='registered_letter', content_handle='contact_check_thank_you', created=ccReg.DateTimeType(date=ccReg.DateType(day=9, month=6, year=2014), hour=8, minute=51, second=30), updated=None, status='ready'),
            Registry.AdminContactVerification.Message(id=1L, type_handle='registered_letter', content_handle='contact_check_notice', created=ccReg.DateTimeType(date=ccReg.DateType(day=9, month=6, year=2014), hour=8, minute=49, second=54), updated=None, status='ready'),
            Registry.AdminContactVerification.Message(id=6L, type_handle='email', content_handle='contact_check_notice', created=ccReg.DateTimeType(date=ccReg.DateType(day=9, month=6, year=2014), hour=8, minute=49, second=54), updated=ccReg.DateTimeType(date=ccReg.DateType(day=9, month=6, year=2014), hour=8, minute=49, second=56), status='sent')
        ]

        tc.go('http://localhost:8080/contactcheck/detail/%s/' % self.check_handle)
        self.verif_mock.getContactCheckMessages.assert_called_once_with(1)
        tc.find('KONTAKT')
        tc.find('running')  # this status is seen only in history
        tc.find('registered_letter')  # list of messages is only in history
        tc.find('All checks of this contact')  # history of all checks

    @enable_corba_comparison_decorator(Registry.AdminContactVerification.ContactTestUpdate)
    def test_tests_and_check_status_change(self):
        tc.go('http://localhost:8080/contactcheck/detail/%s/resolve/' % self.check_handle)
        tc.fv(2, 'email_host_existence', 'fail')

        tc.submit('fail:add_manual')  # submit changes os test states, resolve check as fail and create a new manual Check
        self.verif_mock.updateContactCheckTests.assert_called_once_with(self.check_handle,
            [Registry.AdminContactVerification.ContactTestUpdate('email_host_existence', 'fail')], 0)
        self.verif_mock.resolveContactCheckStatus.assert_called_once_with(self.check_handle, 'fail', 0)
        self.verif_mock.enqueueContactCheck.assert_called_once_with(1, 'manual', 0)


class TestCheckDetailPerms(TestCheckDetailBase):
    def setUp(self):
        super(TestCheckDetailPerms, self).setUp()
        self.authorizer = TestAuthorizer()
        self.monkey_patch(self.web_session_mock['user'], '_authorizer', self.authorizer)

    def test_detail_automatic_perms(self):
        tc.go('http://localhost:8080/contactcheck/detail/%s/' % self.check_handle)
        tc.find('don\'t have permissions')

        self.authorizer.add_perms('read.contactcheck_automatic')
        tc.go('http://localhost:8080/contactcheck/detail/%s/' % self.check_handle)
        tc.notfind('don\'t have permissions')
        tc.notfind('Invalidate')

        tc.go('http://localhost:8080/contactcheck/detail/%s/resolve/' % self.check_handle)
        tc.find('don\'t have permissions')

        self.authorizer.add_perms('change.contactcheck_automatic')
        tc.go('http://localhost:8080/contactcheck/detail/%s/resolve/' % self.check_handle)
        tc.find('Invalidate')
        tc.notfind('Resolve as failed')

        self.authorizer.add_perms('add.contactcheck_manual')
        tc.go('http://localhost:8080/contactcheck/detail/%s/resolve/' % self.check_handle)
        tc.find('Resolve as failed')

    def test_detail_manual_perms(self):
        self.verif_mock.getContactCheckDetail.side_effect = self._get_contact_check_func('manual')

        tc.go('http://localhost:8080/contactcheck/detail/%s/' % self.check_handle)
        tc.find('don\'t have permissions')

        self.authorizer.add_perms('read.contactcheck_manual')
        tc.go('http://localhost:8080/contactcheck/detail/%s/' % self.check_handle)
        tc.notfind('don\'t have permissions')

        tc.go('http://localhost:8080/contactcheck/detail/%s/resolve/' % self.check_handle)
        tc.find('don\'t have permissions')

        self.authorizer.add_perms('change.contactcheck_manual')
        tc.go('http://localhost:8080/contactcheck/detail/%s/resolve/' % self.check_handle)
        tc.find('Invalidate')
        tc.notfind('thank letter')

        self.authorizer.add_perms('add.contactcheck_thank_you')
        tc.go('http://localhost:8080/contactcheck/detail/%s/resolve/' % self.check_handle)
        tc.find('thank letter')
        tc.notfind('Resolve as failed')

    def test_detail_manual_perms_fail_req(self):
        self.authorizer.add_perms('read.contactcheck_manual', 'change.contactcheck_manual')
        self.verif_mock.getContactCheckDetail.side_effect = self._get_contact_check_func('manual', 'fail_req')

        tc.go('http://localhost:8080/contactcheck/detail/%s/resolve/' % self.check_handle)
        tc.notfind('Resolve as failed')

        self.authorizer.add_perms('delete.domain')
        tc.go('http://localhost:8080/contactcheck/detail/%s/resolve/' % self.check_handle)
        tc.find('Resolve as failed')
