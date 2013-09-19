import cherrypy
import mock
from fred_webadmin.corba import Registry
from fred_webadmin.utils import DynamicWrapper

blocking_mock = mock.Mock()
#blocking_mock.__class__ = mock.Mock # so it's pickleable into session data
blocking_mock.getBlockingStatusDescList.return_value = [
    Registry.Administrative.StatusDesc(id=1, shortName='serverDeleteProhibited', name='Delete prohibited'),
    Registry.Administrative.StatusDesc(id=2, shortName='serverRenewProhibited', name='Registration renewal prohibited'),
    Registry.Administrative.StatusDesc(id=3, shortName='serverTransferProhibited', name='Sponsoring registrar change prohibited'),
    Registry.Administrative.StatusDesc(id=4, shortName='serverUpdateProhibited', name='Update prohibited'),
    Registry.Administrative.StatusDesc(id=5, shortName='serverOutzoneManual', name='Domain is administratively kept out of zone'),
    Registry.Administrative.StatusDesc(id=6, shortName='serverInzoneManual', name='Domain is administratively kept in zone'),
]
#def blockDomainsId_mock():
#    pass
#blocking_mock.blockDomainsId.side_effect = blockDomainsId_mock
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
#blocking_mock.blockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_ALREADY_BLOCKED(
#    what=[Registry.Administrative.DomainIdHandle(domainId=22, domainHandle='pepova.cz'),
#          Registry.Administrative.DomainIdHandle(domainId=23, domainHandle='pepkova.cz')])
#blocking_mock.blockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=exc_what_ids)
#blocking_mock.blockDomainsId.side_effect = Registry.Administrative.OWNER_HAS_OTHER_DOMAIN(what=[
#    Registry.Administrative.OwnerDomain(ownerId=1,
#                ownerHandle='THEPEPE',
#                otherDomainList=[Registry.Administrative.DomainIdHandle(domainId=22, domainHandle='pepova.cz'),
#                                 Registry.Administrative.DomainIdHandle(domainId=23, domainHandle='pepkova.cz')]
#                )
#    ])
blocking_mock.updateBlockDomainsId.return_value = None

#blocking_mock.updateBlockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=exc_what_ids)
# blocking_mock.unblockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=exc_what_ids)
# blocking_mock.unblockDomainsId.side_effect = Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS(what='POKUS')
blocking_mock.unblockDomainsId.return_value = None

blocking_mock.restorePreAdministrativeBlockStatesId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=exc_what_ids)
# blocking_mock.restorePreAdministrativeBlockStatesId.side_effect = Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS(what='POKUS')

blocking_mock.blacklistAndDeleteDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=exc_what_ids)
blocking_mock.blacklistAndDeleteDomainsId.return_value = None


def get_blocking_mock():
    return blocking_mock


def mock_blocking():
    cherrypy.session['Blocking'] = DynamicWrapper(get_blocking_mock)
