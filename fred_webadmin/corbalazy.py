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

from corbarecoder import CorbaRecode
recoder = CorbaRecode('utf-8')
c2u = recoder.decode # recode from corba string to unicode
u2c = recoder.encode # recode from unicode to strings

class CorbaLazyRequest(object):
    '''
    Because some classes (as forms) are initialized when start of webadmin, this
    object gets data as late as possible (when needed), so user is already connected
    and connection needed.
    '''
    def __init__(self, object_name, function_name, *args, **kwargs):
        self.object_name = object_name
        self.function_name = function_name
        self.c_args = u2c(args) or []
        self.c_kwargs = u2c(kwargs) or {}
        self.index = -1
        self.data_len = 0 
        self.data = None

    def _convert_data(self, data):
        return data
    
    def _get_data(self):
        debug('CorbaLazyRequest getting data')
        corba_object = cherrypy.session.get(self.object_name)
        corba_func = getattr(corba_object, self.function_name)
        data = c2u(corba_func(*self.c_args, **self.c_kwargs))
        self.data = self._convert_data(data)
        self.data_len = len(self.data)

    def __getattribute__(self, name):
        return super(CorbaLazyRequest, self).__getattribute__(name)
    
    def next(self):
        if self.data is None:
            self._get_data()
        self.index += 1
        if self.index < self.data_len:
            return self.data[self.index]
        else:
            raise StopIteration

#    def __repr__(self):
#        return repr(self._get_result())

#    def __len__(self):
#        return len(self._get_result())

    def __iter__(self):
        #return iter(self._get_result())
        return self
    
    def __str__(self):
        return str(self._get_result())
    
class CorbaLazyRequest1V2L(CorbaLazyRequest):
    '''In corba is list of one value and output is generator of couples of that value: ([x,x] for x in corbaData)'''
    def _convert_data(self, data):
        return [[x, x] for x in data]

# Pokud se ty funkce na getChoices danych enumu nesjednoti, tak muzu udelat potomky CorbaLazyRequest,
#  ktere pretizej metodu _get_result a uz rovnou vratej treba [[x, x] for x in super(JA, self)._get_result()] 
    