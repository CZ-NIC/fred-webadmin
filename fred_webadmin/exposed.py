#!/usr/bin/python
# -*- coding: utf-8 -*-

import types
import traceback
import sys
from fred_webadmin.corba import CorbaServerDisconnectedException
from logging import debug, error

from omniORB import CORBA

from fred_webadmin.customview import CustomView
from fred_webadmin.webwidgets.gpyweb.gpyweb import attr, div, p, pre
from fred_webadmin import config
from fred_webadmin.corba import ccReg, Registry
from translation import _

def catch_webadmin_exceptions_decorator(view_func):
    ''' This decorator is applicated to all view methods of website,
        it catches some permission as PermissionDeniedError'''
    def _wrapper(*args, **kwd):
        self = args[0]
        try:
            return view_func(*args, **kwd)
        except CorbaServerDisconnectedException, e:
            self.remove_session_data()
            return self._render('disconnected')
        except CORBA.TRANSIENT, e:
            error("BACKEND IS NOT RUNNING")
            #raise e
            context = {'message': div()}
            if config.debug:
                context['message'].add(p('''Congratulations! Prave se vam '''
                '''(nebo nekomu pred vami) povedlo shodit backend server, '''
                '''pripiste si plusovy bod!'''))
            else:
                context['message'].add(p(_('Error: Backend server is not running!')))
            context['message'].add(pre(attr( id='traceback'), traceback.format_exc()))    
            return self._render('error', context)
        except ccReg.FileManager.IdNotFound, e:
            error("FILE NOT FOUND %s" % e)

            context = {'message': div()}
            context['message'].add(p(_('''Error: File not found!''')))
            context['message'].add(pre(attr(id='traceback'), traceback.format_exc()))
            return self._render('error', context)
            
        except CustomView, e:
            return e.rendered_view
        
         
    #update_wrapper(_wrapper, view_func)
    return _wrapper



class AdifPageMetaClass(type):
#    def __init__(cls, name, bases, dict):
#        super(AdifPageMetaClass, cls).__init__(name, bases, dict)
#        for name, value in dict.iteritems():
#            if type(value) == types.FunctionType and not name.startswith('_'):
#                value.exposed = True
           
    def __new__(mcs, name, bases, attrs):
        debug('%s|%s|%s|%s' % (mcs, name, bases, attrs))
        #dict[name] = catch_webadmin_exceptions_decorator(value)
        
        for attr_name, attr in attrs.items():
            if type(attr) == types.FunctionType and not attr_name.startswith('_'):
                #attr.exposed = True
                
                attrs[attr_name] = catch_webadmin_exceptions_decorator(attr)
                attrs[attr_name].exposed = True

        new_class = type.__new__(mcs, name, bases, attrs)
        return new_class
    
