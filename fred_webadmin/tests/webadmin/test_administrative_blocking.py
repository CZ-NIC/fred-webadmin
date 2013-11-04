import cherrypy
import mock
from omniORB import CORBA
import twill.commands

from .test_adif import BaseADIFTestCase
from fred_webadmin.corba import Registry, ccReg
from fred_webadmin.tests.webadmin.base import init_test_server, deinit_test_server
from fred_webadmin.tests.webadmin.corba_detail_maker import CorbaDetailMaker
from fred_webadmin.utils import DynamicWrapper


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
    # blocking_mock.blockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=exc_what_ids)
    # blocking_mock.blockDomainsId.side_effect = Registry.Administrative.OWNER_HAS_OTHER_DOMAIN(what=[
    #    Registry.Administrative.OwnerDomain(ownerId=1,
    #                ownerHandle='THEPEPE',
    #                otherDomainList=[Registry.Administrative.DomainIdHandle(domainId=22, domainHandle='pepova.cz'),
    #                                 Registry.Administrative.DomainIdHandle(domainId=23, domainHandle='pepkova.cz')]
    #                )
    #    ])
    blocking_mock.updateBlockDomainsId.return_value = None

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

        def get_detail_side_effect(filter_type, object_id):
            if filter_type == ccReg.FT_DOMAIN:
                return domain_detail
            elif filter_type == ccReg.FT_CONTACT:
                return contact_detail
            elif filter_type == ccReg.FT_REGISTRAR:
                return registrar_detail
            else:
                raise 'This mock getDetail does not know type "%s"' % filter_type
        self.session_mock.getDetail.side_effect = get_detail_side_effect


    def test_not_blocked_domain_detail_buttons(self):
        self._prepare_domain_detail(blocked=False)
        twill.commands.go('http://localhost:8080/domain/detail/?id=1')
        twill.commands.find(self.FILTER_BUTTON_XPATH % 'Block', 'x')
        twill.commands.find(self.FILTER_BUTTON_XPATH % 'Blacklist and delete', 'x')
        twill.commands.notfind(self.FILTER_BUTTON_XPATH % 'Change blocking', 'x')
        twill.commands.notfind(self.FILTER_BUTTON_XPATH % 'Unblock', 'x')


    def test_blocked_domain_detail_buttons(self):
        self._prepare_domain_detail(blocked=True)
        twill.commands.go('http://localhost:8080/domain/detail/?id=1')
        twill.commands.notfind(self.FILTER_BUTTON_XPATH % 'Block', 'x')
        twill.commands.find(self.FILTER_BUTTON_XPATH % 'Blacklist and delete', 'x')
        twill.commands.find(self.FILTER_BUTTON_XPATH % 'Change blocking', 'x')
        twill.commands.find(self.FILTER_BUTTON_XPATH % 'Unblock', 'x')



class BlockingTestBase(BaseADIFTestCase):
    pass

# twill_output = StringIO()
# def setup_module():
#     root = fred_webadmin.controller.adif.prepare_root()
#     wsgiApp = cherrypy.tree.mount(root)
#     cherrypy.config.update({'server.socket_host': '0.0.0.0',
#                              'server.socket_port': 8080,
#                            })
#     cherrypy.server.start()
#     # Redirect HTTP requests.
#     twill.add_wsgi_intercept('localhost', 8080, lambda : wsgiApp)
#     # Keep Twill quiet (suppress normal Twill output).
#     twill.set_output(twill_output)
#
# def teardown_module():
#     # Remove the intercept.
#     twill.remove_wsgi_intercept('localhost', 8080)
#     # Shut down Cherrypy server.
#     cherrypy.server.stop()
