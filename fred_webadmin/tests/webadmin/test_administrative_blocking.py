import cherrypy
import mock
from fred_webadmin.corba import Registry

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
        domainId=573,
        domainHandle='tdomain20130617095920235589i1002.cz',
        oldOwnerId=1,
        oldOwnerHandle='STAROCH',
        newOwnerId=2,
        newOwnerHandle='MLADOCH'
    ),
]
blocking_mock.blockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_ALREADY_BLOCKED(what=[573, 574])
blocking_mock.blockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=[573, 574])
blocking_mock.unblockDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=[573, 574])
blocking_mock.unblockDomainsId.side_effect = Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS(what='POKUS')
blocking_mock.restorePreAdministrativeBlockStatesId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=[573, 574])
blocking_mock.restorePreAdministrativeBlockStatesId.side_effect = Registry.Administrative.NEW_OWNER_DOES_NOT_EXISTS(what='POKUS')
blocking_mock.blacklistDomainsId.side_effect = Registry.Administrative.DOMAIN_ID_NOT_FOUND(what=[573, 574])

class DynamicWrapper(object):
    def __init__(self, get_object_function):
        super(DynamicWrapper, self).__setattr__('_get_object_function', get_object_function)

    def __getattr__(self, name):
        if name == '_get_object_function':
            return super(DynamicWrapper, self).__getattr__(name)
        else:
            return getattr(self._get_object_function(), name)

    def __setattr__(self, name, value):
        setattr(self._get_object_function(), name, value)

def get_blocking_mock():
    return blocking_mock

def mock_blocking():
    cherrypy.session['Blocking'] = DynamicWrapper(get_blocking_mock)
