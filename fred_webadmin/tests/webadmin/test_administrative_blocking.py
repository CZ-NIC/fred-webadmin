import datetime
import urllib2
from  urllib import urlencode

import cherrypy
import mock
import twill.commands as tc

from .test_adif import BaseADIFTestCase
from fred_webadmin.corba import Registry, ccReg
from fred_webadmin.corbarecoder import u2c
from fred_webadmin.tests.webadmin.base import init_test_server, deinit_test_server
from fred_webadmin.tests.webadmin.corba_detail_maker import CorbaDetailMaker
from fred_webadmin.tests.webadmin.test_corbarecoder import Patched_datetype
from fred_webadmin.utils import DynamicWrapper
from nose.tools import assert_equal, assert_in, assert_not_in  # @UnresolvedImport pylint: disable=E0611


def setup_module():
    init_test_server()


def teardown_module():
    deinit_test_server()


def get_blocking_mock():
    ''' Used for mock backend during development, this is not used for automatic tests '''
    blocking_mock = mock.Mock()

    blocking_mock.getBlockingStatusDescList.return_value = [
        Registry.Administrative.StatusDesc(id=1, shortName='serverDeleteProhibited', name='Delete prohibited'),
        Registry.Administrative.StatusDesc(id=2, shortName='serverRenewProhibited', name='Registration renewal prohibited'),
        Registry.Administrative.StatusDesc(id=3, shortName='serverTransferProhibited', name='Sponsoring registrar change prohibited'),
        Registry.Administrative.StatusDesc(id=4, shortName='serverUpdateProhibited', name='Update prohibited'),
        Registry.Administrative.StatusDesc(id=5, shortName='serverOutzoneManual', name='Domain is administratively kept out of zone'),
        Registry.Administrative.StatusDesc(id=6, shortName='serverInzoneManual', name='Domain is administratively kept in zone'),
    ]
    # def blockDomainsId_mock():
    #    pass
    # blocking_mock.blockDomainsId.side_effect = blockDomainsId_mock
    blocking_mock.blockDomainsId.return_value = [
        Registry.Administrative.DomainIdHandleOwnerChange(
            domainId=571,
            domainHandle='fred582318.cz',
            oldOwnerId=1,
            oldOwnerHandle='STAROCH',
            newOwnerId=2,
            newOwnerHandle='MLADOCH'
        ),
    ]

    exc_what_ids = [577, 571]
    # blocking_mock.blockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_ALREADY_BLOCKED(
    #    what=[Registry.Administrative.DomainIdHandle(domainId=22, domainHandle='pepova.cz'),
    #          Registry.Administrative.DomainIdHandle(domainId=23, domainHandle='pepkova.cz')])
    blocking_mock.blockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=exc_what_ids)
    # blocking_mock.blockDomainsId.side_effect = Registry.Administrative.OWNER_HAS_OTHER_DOMAIN(what=[
    #    Registry.Administrative.OwnerDomain(ownerId=1,
    #                ownerHandle='THEPEPE',
    #                otherDomainList=[Registry.Administrative.DomainIdHandle(domainId=22, domainHandle='pepova.cz'),
    #                                 Registry.Administrative.DomainIdHandle(domainId=23, domainHandle='pepkova.cz')]
    #                )
    #    ])
    blocking_mock.updateBlockDomainsId.return_value = []

    # blocking_mock.updateBlockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=exc_what_ids)
    # blocking_mock.unblockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=exc_what_ids)
    # blocking_mock.unblockDomainsId.side_effect = Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS(what='POKUS')
    blocking_mock.unblockDomainsId.return_value = None

    blocking_mock.restorePreAdministrativeBlockStatesId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=exc_what_ids)
    # blocking_mock.restorePreAdministrativeBlockStatesId.side_effect = Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS(what='POKUS')

    blocking_mock.blacklistAndDeleteDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=exc_what_ids)
    blocking_mock.blacklistAndDeleteDomainsId.return_value = None

    return blocking_mock


def mock_blocking():
    ''' Used for mock backend during development, this is not used for automatic tests '''
    cherrypy.session['Blocking'] = DynamicWrapper(get_blocking_mock)


# === Automatic tests code starts here ===

class TestAdministrativeBlockingBase(BaseADIFTestCase):
    def setUp(self):
        super(TestAdministrativeBlockingBase, self).setUp()
        self.admin_mock.createSession('testuser')
        self.session_mock = self.admin_mock.getSession('testSessionString')
        self.blocking_mock = mock.Mock(Registry.Administrative._objref_Blocking)  # pylint: disable=W0212
        self.blocking_mock.getBlockingStatusDescList.return_value = [
            Registry.Administrative.StatusDesc(id=1, shortName='serverDeleteProhibited', name='Delete prohibited'),
            Registry.Administrative.StatusDesc(id=2, shortName='serverRenewProhibited', name='Registration renewal prohibited'),
            Registry.Administrative.StatusDesc(id=3, shortName='serverTransferProhibited', name='Sponsoring registrar change prohibited'),
            Registry.Administrative.StatusDesc(id=4, shortName='serverUpdateProhibited', name='Update prohibited'),
            Registry.Administrative.StatusDesc(id=5, shortName='serverOutzoneManual', name='Domain is administratively kept out of zone'),
            Registry.Administrative.StatusDesc(id=6, shortName='serverInzoneManual', name='Domain is administratively kept in zone'),
        ]

        self.web_session_mock['Blocking'] = self.blocking_mock


class TestButtonInDetails(TestAdministrativeBlockingBase):
    FILTER_BUTTON_XPATH = '//table[@class="filter_panel"]//form[contains(@action, "/blocking_start/")]//input[@value="%s"]'

    def _prepare_domain_detail(self, blocked):
        cdm = CorbaDetailMaker()
        states_ids = [14L, 15L]  # nssetMissing, outzone
        if blocked:
            states_ids.append(7L)  # serverBlocked (used only by administrative blocking)

        domain_detail = cdm.domain('test.cz', states_ids=states_ids)
        contact_detail = cdm.contact('CONTACT1')
        registrar_detail = cdm.registrar('REG-FRED_A')

        def get_detail_side_effect(filter_type, dummy_object_id):
            if filter_type == ccReg.FT_DOMAIN:
                return domain_detail
            elif filter_type == ccReg.FT_CONTACT:
                return contact_detail
            elif filter_type == ccReg.FT_REGISTRAR:
                return registrar_detail
            else:
                raise RuntimeError('This mock getDetail does not know type "%s"' % filter_type)
        self.session_mock.getDetail.side_effect = get_detail_side_effect

    def test_not_blocked_domain_detail_buttons(self):
        self._prepare_domain_detail(blocked=False)

        tc.go('http://localhost:8080/domain/detail/?id=1')
        tc.find(self.FILTER_BUTTON_XPATH % 'Block', 'x')
        tc.find(self.FILTER_BUTTON_XPATH % 'Blacklist and delete', 'x')
        tc.notfind(self.FILTER_BUTTON_XPATH % 'Change blocking', 'x')
        tc.notfind(self.FILTER_BUTTON_XPATH % 'Unblock', 'x')

    def test_blocked_domain_detail_buttons(self):
        self._prepare_domain_detail(blocked=True)
        tc.go('http://localhost:8080/domain/detail/?id=1')
        tc.notfind(self.FILTER_BUTTON_XPATH % 'Block', 'x')
        tc.find(self.FILTER_BUTTON_XPATH % 'Blacklist and delete', 'x')
        tc.find(self.FILTER_BUTTON_XPATH % 'Change blocking', 'x')
        tc.find(self.FILTER_BUTTON_XPATH % 'Unblock', 'x')


class TestAdministrativeBlockingStart(TestAdministrativeBlockingBase):
    def setUp(self):
        super(TestAdministrativeBlockingStart, self).setUp()
        pagetable_mock = mock.Mock(name='Pagetable mock')
        pagetable_mock.getColumnHeaders.return_value = []
        pagetable_mock._get_page.return_value = 0  # pylint: disable=W0212
        pagetable_mock._get_row.return_value = []  # pylint: disable=W0212
        pagetable_mock._get_numRows.return_value = 0  # pylint: disable=W0212
        pagetable_mock.getSortedBy.return_value = (0, False)
        self.session_mock.getPageTable.return_value = pagetable_mock

    def get_mechanized_browser(self):
        # needed because twill doesn't have public interface for disabling following HTTP redirects
        # and sending POST requests without filling form
        mb = tc.get_browser()._browser  # pylint: disable=W0212
        return mb

    def test_block_start_no_domain_selected(self):
        mb = self.get_mechanized_browser()
        mb.set_handle_redirect(False)
        try:
            post_data = urlencode({'pre_blocking_form': '1',
                                   'blocking_action': 'block',
                                  })
            assert_not_in('pre_blocking_form_data', self.web_session_mock)
            try:
                response = mb.open('http://localhost:8080/domain//filter/blocking_start/', post_data)
            except urllib2.HTTPError, response_redirect:
                response = response_redirect
            assert_in('You must select at least one domain!', response.get_data())
            assert_not_in('pre_blocking_form_data', self.web_session_mock)
        finally:
            mb.set_handle_redirect(True)

    def test_block_start_ok(self):
        mb = self.get_mechanized_browser()
        mb.set_handle_redirect(False)
        try:
            post_data = urlencode({'pre_blocking_form': '1',
                                   'blocking_action': 'block',
                                   'object_selection': '1'
                                  })
            assert_not_in('pre_blocking_form_data', self.web_session_mock)
            try:
                response = mb.open('http://localhost:8080/domain//filter/blocking_start/', post_data)
            except urllib2.HTTPError, response_redirect:
                response = response_redirect
            assert_equal(response.info().getheader('location'), 'http://localhost:8080/domain/blocking/')
            assert_in('pre_blocking_form_data', self.web_session_mock)
        finally:
            mb.set_handle_redirect(True)


class TestAdministrativeBlockingView(TestAdministrativeBlockingBase):
    def test_blocking_view_no_data_in_session(self):
        tc.go('http://localhost:8080/domain/blocking/')
        tc.find('This page is accessible only by posting a blocking form.')


class BaseTestAdministrativeBlockingAction(TestAdministrativeBlockingBase):
    REASON_TEXT = 'Because I can!'
    START_URL = 'http://localhost:8080/domain/blocking/'
    BLOCKING_ACTION = None  # redefined in descendants

    def setUp(self):
        super(BaseTestAdministrativeBlockingAction, self).setUp()
        self.web_session_mock['pre_blocking_form_data'] = {
            'pre_blocking_form': '1',
            'blocking_action': self.BLOCKING_ACTION,
            'object_selection': '1'
        }
        cdm = CorbaDetailMaker()
        self.session_mock.getDetail.side_effect = lambda obj_type, id: cdm.domain('test%s.cz' % id)

        tc.go(self.START_URL)
        tc.showforms()
        tc.fv(2, 'reason', self.REASON_TEXT)

    def test_no_reason(self):
        tc.fv(2, 'reason', '')
        tc.submit()
        tc.find('This field is required.')


class TestAdministrativeBlock(BaseTestAdministrativeBlockingAction):
    BLOCKING_ACTION = 'block'

    def test_submit_default_data(self):
        self.blocking_mock.blockDomainsId.return_value = []

        tc.submit()
        tc.code(200)
        tc.find('successful')

        self.blocking_mock.blockDomainsId.assert_called_once_with(
            [1],
            ['serverDeleteProhibited', 'serverTransferProhibited', 'serverUpdateProhibited'],
            Registry.Administrative.KEEP_OWNER,
            None,
            self.REASON_TEXT,
            0
        )

    def test_block_change_owner_in_result(self):
        self.blocking_mock.blockDomainsId.return_value = [
            Registry.Administrative.DomainIdHandleOwnerChange(
                domainId=1, domainHandle='test1.cz',
                oldOwnerId=1, oldOwnerHandle='STAROCH',
                newOwnerId=2, newOwnerHandle='MLADOCH'
            ),
        ]
        tc.submit()
        tc.code(200)
        tc.find('successful')
        tc.find('STAROCH')
        tc.find('MLADOCH')
        self.blocking_mock.blockDomainsId.assert_called_once_with(
            [1],
            ['serverDeleteProhibited', 'serverTransferProhibited', 'serverUpdateProhibited'],
            Registry.Administrative.KEEP_OWNER,
            None,
            self.REASON_TEXT,
            0
        )

    def test_block_to_date_past(self):
        tc.fv(2, 'block_to_date', '2000-01-01')
        tc.submit()
        tc.url('http://localhost:8080/domain/blocking/')
        tc.find('Block to date must be in the future.')

    def test_form_other_data(self):
        tc.fv(2, 'blocking_status_list', '-serverDeleteProhibited')
        tc.fv(2, 'blocking_status_list', 'serverRenewProhibited')
        tc.fv(2, 'owner_block_mode', '2')

        self.blocking_mock.blockDomainsId.return_value = []
        tc.submit()
        tc.code(200)
        tc.find('successful')

        self.blocking_mock.blockDomainsId.assert_called_once_with(
            [1],
            ['serverRenewProhibited', 'serverTransferProhibited', 'serverUpdateProhibited'],
            Registry.Administrative.BLOCK_OWNER_COPY,
            None,
            self.REASON_TEXT,
            0
        )

    def test_domain_not_found(self):
        self.blocking_mock.blockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=[1])
        tc.submit()
        tc.url(self.START_URL)
        tc.find('Domain\(s\) with id 1 not found\.')

    def test_domain_already_blocked(self):
        self.blocking_mock.blockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_ALREADY_BLOCKED(
            what=[Registry.Administrative.DomainIdHandle(domainId=1, domainHandle='test1.cz'), ])
        tc.submit()
        tc.url(self.START_URL)
        tc.find('Domain\(s\) test1.cz are already blocked\.')

    def test_owner_has_other_domain(self):
        self.blocking_mock.blockDomainsId.side_effect = Registry.Administrative.OWNER_HAS_OTHER_DOMAIN(what=[
            Registry.Administrative.OwnerDomain(ownerId=1,
                        ownerHandle='THEPEPE',
                        otherDomainList=[Registry.Administrative.DomainIdHandle(domainId=1, domainHandle='test1.cz')]
                        )])

        tc.submit()
        tc.url(self.START_URL)
        tc.find('Cannot block holder')


class TestAdministrativeChangeBlocking(BaseTestAdministrativeBlockingAction):
    BLOCKING_ACTION = 'change_blocking'

    def test_submit_default_data(self):
        tc.submit()
        tc.code(200)
        tc.find('successful')

        self.blocking_mock.updateBlockDomainsId.assert_called_once_with(
            [1],
            ['serverDeleteProhibited', 'serverTransferProhibited', 'serverUpdateProhibited'],
            None,
            self.REASON_TEXT,
            0
        )

    def test_with_other_data(self):
        block_to_date = datetime.date.today() + datetime.timedelta(1)
        tc.fv(2, 'block_to_date', block_to_date.isoformat())
        tc.fv(2, 'blocking_status_list', '-serverTransferProhibited')
        tc.fv(2, 'blocking_status_list', '-serverUpdateProhibited')
        tc.fv(2, 'blocking_status_list', 'serverRenewProhibited')
        tc.submit()
        tc.code(200)
        tc.find('successful')

        self.blocking_mock.updateBlockDomainsId.assert_called_once_with(
            [1],
            ['serverDeleteProhibited', 'serverRenewProhibited'],
            Patched_datetype(block_to_date.day, block_to_date.month, block_to_date.year),
            self.REASON_TEXT,
            0
        )

    def test_domain_not_found(self):
        self.blocking_mock.updateBlockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=[1])
        tc.submit()
        tc.url(self.START_URL)
        tc.find('Domain\(s\) with id 1 not found\.')

    def test_domain_not_blocked(self):
        self.blocking_mock.updateBlockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_BLOCKED(
            what=[Registry.Administrative.DomainIdHandle(domainId=1, domainHandle='test1.cz'), ])
        tc.submit()
        tc.url(self.START_URL)
        tc.find('Domain\(s\) test1.cz not blocked\.')


class TestAdministrativeUnblock(BaseTestAdministrativeBlockingAction):
    BLOCKING_ACTION = 'unblock'

    def test_unblock_success(self):
        tc.fv(2, 'new_holder', 'KONTAKT')
        tc.submit()
        tc.code(200)
        tc.find('successful')

        self.blocking_mock.unblockDomainsId.assert_called_once_with(
            [1],
            'KONTAKT',
            False,
            self.REASON_TEXT,
            0
        )

    def test_unblock_missing_handle(self):
        tc.submit()
        tc.code(200)
        tc.find('New holder is required when you don\'t use "Restore prev. state"')

    def test_unblock_remove_admin_contacts(self):
        tc.fv(2, 'new_holder', 'KONTAKT')
        tc.fv(2, 'remove_admin_contacts', True)
        tc.submit()
        tc.code(200)
        tc.find('successful')

        self.blocking_mock.unblockDomainsId.assert_called_once_with(
            [1],
            'KONTAKT',
            True,
            self.REASON_TEXT,
            0
        )

    def test_unblock_domain_not_found(self):
        tc.fv(2, 'new_holder', 'KONTAKT')
        self.blocking_mock.unblockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=[1])
        tc.submit()
        tc.url(self.START_URL)
        tc.find(r'Domain\(s\) with id 1 not found\.')

    def test_unblock_domain_not_blocked(self):
        tc.fv(2, 'new_holder', 'KONTAKT')
        self.blocking_mock.unblockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_BLOCKED(
            what=[Registry.Administrative.DomainIdHandle(domainId=1, domainHandle='test1.cz'), ])
        tc.submit()
        tc.url(self.START_URL)
        tc.find(r'Domain\(s\) test1.cz not blocked\.')

    def test_unblock_holder_not_exists(self):
        tc.fv(2, 'new_holder', 'KONTAKT')
        self.blocking_mock.unblockDomainsId.side_effect = Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS(
            what='KONTAKT')
        tc.submit()
        tc.url(self.START_URL)
        tc.find(r'New holder KONTAKT does not exists.')

    def test_restore_success(self):
        tc.fv(2, 'restore_prev_state', True)
        tc.submit()
        tc.code(200)
        tc.find('successful')

        self.blocking_mock.restorePreAdministrativeBlockStatesId.assert_called_once_with(
            [1],
            '',
            self.REASON_TEXT,
            0
        )

    def test_restore_error_when_use_remove_admin_contact(self):
        tc.fv(2, 'restore_prev_state', True)
        tc.fv(2, 'remove_admin_contacts', True)
        tc.submit()
        tc.code(200)
        tc.find('You cannot use "Remove admin. contacts" and "Restore prev. state" at the same time.')

    def test_restore_with_new_holder(self):
        tc.fv(2, 'restore_prev_state', True)
        tc.fv(2, 'new_holder', 'KONTAKT')
        tc.submit()
        tc.code(200)
        tc.find('successful')

        self.blocking_mock.restorePreAdministrativeBlockStatesId.assert_called_once_with(
            [1],
            'KONTAKT',
            self.REASON_TEXT,
            0
        )

    def test_restore_domain_not_found(self):
        tc.fv(2, 'restore_prev_state', True)
        self.blocking_mock.restorePreAdministrativeBlockStatesId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=[1])
        tc.submit()
        tc.url(self.START_URL)
        tc.find(r'Domain\(s\) with id 1 not found\.')

    def test_restore_domain_not_blocked(self):
        tc.fv(2, 'restore_prev_state', True)
        self.blocking_mock.restorePreAdministrativeBlockStatesId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_BLOCKED(
            what=[Registry.Administrative.DomainIdHandle(domainId=1, domainHandle='test1.cz'), ])
        tc.submit()
        tc.url(self.START_URL)
        tc.find(r'Domain\(s\) test1.cz not blocked\.')

    def test_restore_holder_not_exists(self):
        tc.fv(2, 'restore_prev_state', True)
        tc.fv(2, 'new_holder', 'KONTAKT')
        self.blocking_mock.restorePreAdministrativeBlockStatesId.side_effect = Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS(
            what='KONTAKT')
        tc.submit()
        tc.url(self.START_URL)
        tc.find(r'New holder KONTAKT does not exists.')


class TestAdministrativeBlacklistAndDelete(BaseTestAdministrativeBlockingAction):
    BLOCKING_ACTION = 'blacklist_and_delete'

    def setUp(self):
        super(TestAdministrativeBlacklistAndDelete, self).setUp()
        self.web_session_mock['history'] = False

    def test_success(self):
        tc.submit()
        tc.code(200)
        tc.find('successful')

        self.blocking_mock.blacklistAndDeleteDomainsId.assert_called_once_with(
            [1],
            None,
            self.REASON_TEXT,
            0
        )

    def test_block_to_date_in_past(self):
        blacklist_to_date = datetime.date.today() - datetime.timedelta(1)
        tc.fv(2, 'blacklist_to_date', blacklist_to_date.isoformat())
        tc.submit()
        tc.code(200)
        tc.find('Blacklist to date must be in the future.')

    def test_blacklist_to_date_ok(self):
        blacklist_to_date = datetime.date.today() + datetime.timedelta(1)
        tc.fv(2, 'blacklist_to_date', blacklist_to_date.isoformat())
        tc.submit()
        tc.code(200)
        tc.find('successful')

        self.blocking_mock.blacklistAndDeleteDomainsId.assert_called_once_with(
            [1],
            Patched_datetype(blacklist_to_date.day, blacklist_to_date.month, blacklist_to_date.year),
            self.REASON_TEXT,
            0
        )

    def test_domain_not_found(self):
        self.blocking_mock.blacklistAndDeleteDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=[1])
        tc.submit()
        tc.url(self.START_URL)
        tc.find(r'Domain\(s\) with id 1 not found\.')
