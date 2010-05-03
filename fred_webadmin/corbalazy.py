'''
This module connects to corba and retrieves data, 
that are needed befor any user logs in,
so before connectoin to concrete corba server choosen by user.
Thus this data should be only constant (same for all server) as action type etc.
at least for given version of server (all servers shoud be same version).
'''

import config
import cherrypy
import omniORB
from logging import debug
import sys
from corbarecoder import DaphneCorbaRecode
import fred_webadmin.corbarecoder as recoder
from fred_webadmin.corba import ccReg

class ServerNotAvailableError(Exception):
    """ CORBA server could not be connected to. 
    """
    pass

class CorbaLazyRequest(object):
    def __init__(self, object_name, mgr_getter_name, function_name, *args, **kwargs):
        self.object_name = object_name
        self.function_name = function_name
        self.mgr_getter_name = mgr_getter_name
        self.c_args = recoder.u2c(args) or []
        self.c_kwargs = recoder.u2c(kwargs) or {}
        self.data = None
    
    def _convert_data(self, data):
        return data
    
    def _get_data(self):
        """ Get data from CORBA and cache it to self.data, next call is ignored,
            because data are already cached.
        """
        if self.data is None:
            debug('CorbaLazyRequest getting data')
            corba_object = cherrypy.session.get(self.object_name)
            if self.mgr_getter_name:
                """#TODO(tom): Remove mock when implemented on server
                class MockGroupManager(object):
                    def getGroups(self):
                        from fred_webadmin.corba import Registry
                        from fred_webadmin.nulltype import NullDate
                        return [Registry.Registrar.Group.GroupData(
                            42L, "test group", ccReg.DateType(0,0,0))]
                cherrypy.session["Admin"].getGroupManager = (lambda :
                MockGroupManager())"""
                corba_object = getattr(corba_object, self.mgr_getter_name)()
            corba_func = getattr(corba_object, self.function_name)
            try:
                data = recoder.c2u(corba_func(*self.c_args, **self.c_kwargs))
            except (omniORB.CORBA.SystemException,
                ccReg.Admin.ServiceUnavailable), e:
                raise ServerNotAvailableError(e)
            self.data = self._convert_data(data)
        
    def __str__(self):
        self._get_data()
        return str(self.data)
    
    def __repr__(self):
        return self.__str__()
            
class CorbaLazyRequestIter(CorbaLazyRequest):
    '''
    Because some classes (as forms) are initialized when start of webadmin, this
    object gets data as late as possible (when needed), so user is already connected
    (connection is needed for this).
    '''
    def __init__(self, object_name, mgr_getter_name, function_name, *args, **kwargs):
        super(CorbaLazyRequestIter, self).__init__(object_name, mgr_getter_name, function_name, *args, **kwargs)
        self.index = -1
        self.data_len = 0 
    
    def _get_data(self):
        super(CorbaLazyRequestIter, self)._get_data()
        self.data_len = len(self.data)

    def next(self):
        self._get_data()
        self.index += 1
        if self.index < self.data_len:
            return self.data[self.index]
        else:
            self.index = -1
            raise StopIteration
        
    def insert(self, index, obj):
        self._get_data()
        self.data.insert(index, obj)
    
    def pop(self, index):
        self._get_data()
        return self.data.pop(index)

    
    def __getitem__(self, index):
        self._get_data()
        return self.data[index]

    def __len__(self):
        self._get_data()
        return self.data_len

    def __iter__(self):
        return self
    
    
class CorbaLazyRequest1V2L(CorbaLazyRequestIter):
    '''In corba is list of one value and output is generator of couples of that value: ([x,x] for x in corbaData)'''
    def _convert_data(self, data):
        return [[x, x] for x in data]
    
class CorbaLazyRequestIterStruct(CorbaLazyRequestIter):
    def __init__(self, object_name, mgr_getter_name, function_name, mapping, *args, **kwargs):
        super(CorbaLazyRequestIterStruct, self).__init__(
            object_name, mgr_getter_name, function_name, *args, **kwargs)
        if len(mapping) == 2:
            self.mapping = mapping
        else:
            raise RuntimeError('CorbaLazyRequestFromStruct __init__: parametr mapping must be list or tupple with length exactly 2.')
    def _convert_data(self, data):
        result = []
        for item in data:
            result_item = []
            for attr_name in self.mapping:
                result_item.append(getattr(item, attr_name))
            result.append(result_item)
        return result


class CorbaLazyRequestIterStructToDict(CorbaLazyRequestIterStruct):
    def _convert_data(self, data):
        result = super(CorbaLazyRequestIterStructToDict, self)._convert_data(data)
        return dict(result)
