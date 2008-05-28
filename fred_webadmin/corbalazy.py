'''
This module connects to corba and retrieves data, 
that are needed befor any user logs in,
so before connectoin to concrete corba server choosen by user.
Thus this data should be only constant (same for all server) as action type etc.
at least for given version of server (all servers shoud be same version).
'''

import config
import cherrypy
from logging import debug
import sys

sys.path.insert(0, '')

from corbarecoder import CorbaRecode
recoder = CorbaRecode('utf-8')
c2u = recoder.decode # recode from corba string to unicode
u2c = recoder.encode # recode from unicode to strings

class CorbaLazyRequest(object):
    def __init__(self, object_name, function_name, *args, **kwargs):
        self.object_name = object_name
        self.function_name = function_name
        self.c_args = u2c(args) or []
        self.c_kwargs = u2c(kwargs) or {}
        self.data = None
    
    def _convert_data(self, data):
        return data
    
    def _get_data(self):
        ''' Get data from CORBA and cache it to self.data, next call is ignored, because data are already cached.  '''
        if self.data is None:
            debug('CorbaLazyRequest getting data')
            corba_object = cherrypy.session.get(self.object_name)
            corba_func = getattr(corba_object, self.function_name)
            data = c2u(corba_func(*self.c_args, **self.c_kwargs))
            self.data = self._convert_data(data)
            #debug('Data are(after conversion): %s' % self.data)
        
    def __str__(self):
        self._get_data()
        return str(self.data)
    
    def __repr__(self):
        return self.__str__()
            
class CorbaLazyRequestIter(CorbaLazyRequest):
    '''
    Because some classes (as forms) are initialized when start of webadmin, this
    object gets data as late as possible (when needed), so user is already connected
    and connection needed.
    '''
    def __init__(self, object_name, function_name, *args, **kwargs):
        super(CorbaLazyRequestIter, self).__init__(object_name, function_name, *args, **kwargs)
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
            self.index = 0
            raise StopIteration


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
    def __init__(self, object_name, function_name, mapping, *args, **kwargs):
        super(CorbaLazyRequestIterStruct, self).__init__(object_name, function_name, *args, **kwargs)
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
