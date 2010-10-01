#!/usr/bin/python
# -*- coding: utf-8 -*-

# system imports
import sys
# extension imports
import omniORB
#import omniORB.codesets
import CosNaming
#from omniORB import CORBA, importIDL

from translation import _

# own exceptions
class IorNotFoundError(Exception):
    pass
class AlreadyLoggedInError(Exception):
    pass
class NotLoggedInError(Exception):
    pass
class LanguageNotSupportedError(Exception):
    pass
class SetLangAfterLoginError(Exception):
    pass
class ParameterIsNotListOrTupleError(Exception):
    pass

class CorbaServerDisconnectedException(Exception):
    pass

def transientFailure(cookie, retries, exc):
    if retries > 10:
        return False
    else:
        return True

def commFailure(cookie, retries, exc):
    if retries > 20:
        return False
    else:
        return True

def systemFailure(cookie, retries, exc):
    if retries > 5:
        return False
    else:
        return True

cookie = None

omniORB.installTransientExceptionHandler(cookie, transientFailure)
omniORB.installCommFailureExceptionHandler(cookie, commFailure)
#omniORB.installSystemExceptionHandler(cookie, systemFailure)

import config
#module_name = importIDL(config.idl)[0] # this hase to be here because cherrypy session needs to know ccReg module on start (while loadin session from file)
omniORB.importIDL(config.idl)
ccReg = sys.modules['ccReg']
Registry = sys.modules['Registry']
orb = omniORB.CORBA.ORB_init(["-ORBnativeCharCodeSet", "UTF-8"], omniORB.CORBA.ORB_ID)
#orb = CORBA.ORB_init(["-ORBnativeCharCodeSet", "UTF-8", "-ORBtraceLevel", "10"], CORBA.ORB_ID)
#omniORB.setClientCallTimeout(2000)

# invoice types (used both in IterTabe and ADIF)
invoices = [
        #{'type': _('All'), 'obj': Registry.Invoicing.IT_NONE},
        {'type': _('Advance'), 'obj': Registry.Invoicing.IT_ADVANCE},
        {'type': _('Account'), 'obj': Registry.Invoicing.IT_ACCOUNT},
]
ccReg.Invoicing.Invoices = invoices # XXX - future lang switching

class Corba(object):
    def __init__(self):
        object.__init__(self)
        #self.module = sys.modules[module_name] #sys.modules[
            #importIDL(idl or os.path.join(os.path.dirname(os.path.abspath(__file__)), IDL_FILE))[0]
            #]
        self.context = None
        
    def connect(self, ior = 'localhost', context_name = 'fred'):
        obj = orb.string_to_object('corbaname::' + ior)
        self.context = obj._narrow(CosNaming.NamingContext)
        self.context_name = context_name

    def getObjectUsingContext(self, component, name, idl_type_str):
        cosname = [CosNaming.NameComponent(component, "context"), CosNaming.NameComponent(name, "Object")]
        obj = self.context.resolve(cosname)
        
        # get idl type from idl_type_str:
        idl_type_parts = idl_type_str.split('.')
        idl_type = sys.modules[idl_type_parts[0]]
        for part in idl_type_parts[1:]:
            idl_type = getattr(idl_type, part)
            
        return obj._narrow(idl_type)

    def getObject(self, name, idltype):
        return self.getObjectUsingContext(self.context_name, name, idltype)
