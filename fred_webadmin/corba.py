#!/usr/bin/python
# -*- coding: utf-8 -*-

# system imports
import sys
# extension imports
import omniORB
import CosNaming

from fred_idl import Registry, ccReg

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

handler_cookie = None

omniORB.installTransientExceptionHandler(handler_cookie, transientFailure)
omniORB.installCommFailureExceptionHandler(handler_cookie, commFailure)
# omniORB.installSystemExceptionHandler(handler_cookie, systemFailure)

orb = omniORB.CORBA.ORB_init(["-ORBnativeCharCodeSet", "UTF-8"], omniORB.CORBA.ORB_ID)


class Corba(object):
    def __init__(self):
        object.__init__(self)
        self.context = None

    def connect(self, ior='localhost', context_name='fred'):
        obj = orb.string_to_object('corbaname::' + ior)
        self.context = obj._narrow(CosNaming.NamingContext)
        self.context_name = context_name

    def getObjectUsingContext(self, component, name, idl_type_str):
        cosname = [CosNaming.NameComponent(component, "context"), CosNaming.NameComponent(name, "Object")]
        obj = self.context.resolve(cosname)

        # get idl type from idl_type_str:
        idl_type_parts = idl_type_str.split('.')
        idl_type = sys.modules['fred_idl.' + idl_type_parts[0]]
        for part in idl_type_parts[1:]:
            idl_type = getattr(idl_type, part)

        return obj._narrow(idl_type)

    def getObject(self, name, idltype):
        return self.getObjectUsingContext(self.context_name, name, idltype)
