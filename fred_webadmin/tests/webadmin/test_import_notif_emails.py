import os
import twill.commands as tc

from mock import Mock, call
from nose.tools import assert_equal

from fred_webadmin.corba import Registry
from fred_webadmin.tests.webadmin.test_adif import BaseADIFTestCase
from fred_webadmin.tests.webadmin.base import enable_corba_comparison_decorator, init_test_server, deinit_test_server


def setup_module():
    init_test_server()


def teardown_module():
    deinit_test_server()


class TestImportNotifEmails(BaseADIFTestCase):
    def setUp(self):
        super(TestImportNotifEmails, self).setUp()
        self.admin_mock.createSession('testuser')
        self.session_mock = self.admin_mock.getSession('testSessionString')
        self.notif_mock = Mock(Registry.Notification._objref_Server)  # pylint: disable=W0212
        self.web_session_mock['Notification'] = self.notif_mock
        tc.go('http://localhost:8080/domain/import_notif_emails/')

    def test_file_not_uploaded(self):
        tc.fv(2, 'submit', '')
        tc.submit()
        tc.find('This field is required.')

    def test_empty_file_uploaded(self):
        tc.formfile(2, 'domains_emails', os.path.join(os.path.dirname(__file__),
                                                      'data/empty_file'))
        tc.submit()
        tc.find('Wrong file format.')

    def test_file_with_invalid_id(self):
        tc.formfile(2, 'domains_emails', os.path.join(os.path.dirname(__file__),
                                                      'data/domain_2016-09-16_invalid_id.csv'))
        tc.submit()
        tc.find('Invalid value in column Id: "asdf9". It must be a whole number.')

    @enable_corba_comparison_decorator(Registry.Notification.DomainEmail)
    def test_file_ok(self):
        tc.formfile(2, 'domains_emails', os.path.join(os.path.dirname(__file__),
                                                      'data/domain_2016-09-16_OK.csv'))
        tc.submit()
        assert_equal(
            self.notif_mock.mock_calls,
            [call.set_domain_outzone_unguarded_warning_emails([
                Registry.Notification.DomainEmail(domain_id=4, email='poks1@nic.cz'),
                Registry.Notification.DomainEmail(domain_id=9, email='pokus2@nic.cz'),
                Registry.Notification.DomainEmail(domain_id=9, email='pokus3@nic.cz')])]
        )
        tc.find(r'Emails have been successfully saved. \(2 domains, 3 emails\)')

    @enable_corba_comparison_decorator(Registry.Notification.DomainEmail)
    def test_file_invalid_email(self):
        self.notif_mock.set_domain_outzone_unguarded_warning_emails.side_effect = \
            Registry.Notification.DOMAIN_EMAIL_VALIDATION_ERROR(
                [Registry.Notification.DomainEmail(domain_id=4, email='pok@s1@nic.cz')]
            )
        tc.formfile(2, 'domains_emails', os.path.join(os.path.dirname(__file__),
                                                      'data/domain_2016-09-16_ERR.csv'))
        tc.submit()
        assert_equal(
            self.notif_mock.mock_calls,
            [call.set_domain_outzone_unguarded_warning_emails([
                Registry.Notification.DomainEmail(domain_id=4, email='pok@s1@nic.cz'),
                Registry.Notification.DomainEmail(domain_id=9, email='pokus2@nic.cz'),
                Registry.Notification.DomainEmail(domain_id=9, email='pokus3@nic.cz')])]
        )
        tc.find('The file contains these invalid emails: pok@s1@nic.cz')
