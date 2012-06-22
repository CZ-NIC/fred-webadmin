#!/usr/bin/python
# -*- coding: utf-8 -*-

import types
import traceback
import CosNaming
from fred_webadmin.corba import CorbaServerDisconnectedException
from logging import debug, error

from omniORB import CORBA

from fred_webadmin.customview import CustomView
from fred_webadmin.webwidgets.gpyweb.gpyweb import attr, div, p, pre
from fred_webadmin import config
from fred_webadmin.corba import ccReg
from fred_webadmin.translation import _

def catch_webadmin_exceptions_decorator(view_func):
    ''' This decorator is applicated to all view methods of website,
        it catches some permission as PermissionDeniedError'''
    def _wrapper(*args, **kwd):
        self = args[0]
        try:
            return view_func(*args, **kwd)
        except CorbaServerDisconnectedException, e:
            self._remove_session_data()
            return self._render('disconnected')
        except CORBA.TRANSIENT, e:
            error("BACKEND IS NOT RUNNING")
            context = {'message': div()}
            if config.debug:
                context['message'].add(p('''Congratulations! Prave se vam '''
                '''(nebo nekomu pred vami) povedlo shodit backend server, '''
                '''pripiste si plusovy bod!'''))
            else:
                context['message'].add(
                    p(_('Error: Backend server is not running!')))
            context['message'].add(
                pre(attr(id='traceback'), traceback.format_exc()))
            return self._render('error', context)
        except CORBA.UNKNOWN, e:
            error("Exception CORBA.UNKNOWN!")
            context = {'message': div()}
            if config.debug:
                context['message'].add(p('''Congratulations! Prave se vam '''
                '''povedlo na backend serveru vyvolat neocekavanou vyjimku, '''
                '''k cemuz samozrejme nikdy nemuze dojit!'''))
            else:
                context['message'].add(
                    p(_('Error: Unknown backend server exception!')))
            context['message'].add(
                pre(attr(id='traceback'), traceback.format_exc()))
            return self._render('error', context)
        except ccReg.FileManager.IdNotFound, e:
            error("FILE NOT FOUND %s" % e)

            context = {'message': div()}
            context['message'].add(p(_('''Error: File not found!''')))
            context['message'].add(
                pre(attr(id='traceback'), traceback.format_exc()))
            return self._render('error', context)
        except CosNaming.NamingContext.NotFound, e:
            context = {'message': div()}
            context['message'].add(
                p(_('Error: CORBA object could not be found!')))
            context['message'].add(
                pre(attr(id='traceback'), traceback.format_exc()))
            return self._render('error', context)
        except CustomView, e:
            return e.rendered_view
    return _wrapper



class AdifPageMetaClass(type):
    def __new__(mcs, name, bases, attrs):
        for attr_name, attr in attrs.items():
            if type(attr) == types.FunctionType and not attr_name.startswith('_'):
                attrs[attr_name] = catch_webadmin_exceptions_decorator(attr)
                attrs[attr_name].exposed = True
        new_class = type.__new__(mcs, name, bases, attrs)
        return new_class
