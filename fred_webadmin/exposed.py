#!/usr/bin/python
# -*- coding: utf-8 -*-

import types
import adif
from decorator import update_wrapper
from omniORB import CORBA

def catch_webadmin_exceptions_decorator(view_func):
    ''' This decorator is applicated to all view methods of website,
        it catches some permission as PermissionDeniedError'''
    def _wrapper(*args, **kwd):
        self = args[0]
        try:
            return view_func(*args, **kwd)
#        except adif.PermissionDeniedError, e:
#            return e.message
#        except adif.CorbaServerDisconnectedException, e:
#            return e.message
        except CORBA.TRANSIENT, e:
            print "BACKEND NEBEZIIII:", self._get_menu_handle('error')
            #e.message += '''Congratulations! Prave se vam povedlo schodit backend server, pripiste si plusovy bod'''
            raise e
         
    #update_wrapper(_wrapper, view_func)
    return _wrapper



class AdifPageMetaClass(type):
#    def __init__(cls, name, bases, dict):
#        super(AdifPageMetaClass, cls).__init__(name, bases, dict)
#        for name, value in dict.iteritems():
#            if type(value) == types.FunctionType and not name.startswith('_'):
#                value.exposed = True
           
    def __new__(cls, name, bases, attrs):
        print cls, '|',  name, '|', bases, '|', attrs
        #dict[name] = catch_webadmin_exceptions_decorator(value)
        
        for attr_name, attr in attrs.items():
            if type(attr) == types.FunctionType and not attr_name.startswith('_'):
                attr.exposed = True
                #attrs[attr_name] = catch_webadmin_exceptions_decorator(attr)
                

        new_class = type.__new__(cls, name, bases, attrs)
        return new_class