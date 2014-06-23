import types
import cherrypy

import fred_webadmin as fred

from fred_webadmin.utils import get_current_url
from fred_webadmin.webwidgets.gpyweb.gpyweb import div, p, br
from fred_webadmin.translation import _
import fred_webadmin.utils as utils

from fred_webadmin.webwidgets.templates.pages import BaseSiteMenu
from fred_webadmin.customview import CustomView


def login_required(view_func):
    ''' decorator for login-required pages '''
    def _wrapper(*args, **kwd):
        if cherrypy.session.get('user', None):
            return view_func(*args, **kwd)
        redir_addr = '/login/?next=%s' % get_current_url(cherrypy.request)
        raise cherrypy.HTTPRedirect(redir_addr)
    return _wrapper


def check_nperm_func(nperms, nperm_type='all', raise_err=False):
    ''' Like check_nperm decorator, but it's normal function, used when you cannot use as decorator, for example
        when you need to get permission from string from other object, which is instantiated in the function.
    '''
    user = cherrypy.session.get('user', None)
    if user:
        utils.details_cache = {}  # invalidate details cache
        if not user.check_nperms(nperms, nperm_type):
            return True
        else:
            if raise_err:
                context = {'main': div()}
                context['main'].add(
                    p(_("You don't have permissions for this page!")))
                if fred.config.debug:
                    context['main'].add(
                        p('nperms=%s, nperm_type=%s' % (
                            nperms, nperm_type)))
                raise CustomView(BaseSiteMenu(context).render())
            else:
                return False
    else:
        redir_addr = '/login/?next=%s' % get_current_url(cherrypy.request)
        raise cherrypy.HTTPRedirect(redir_addr)


def check_nperm(nperms, nperm_type='all'):
    ''' decorator for login-required and negative permissions check '''
    def _decorator(view_func):
        def _wrapper(*args, **kwd):
            user = cherrypy.session.get('user', None)
            if user:
                utils.details_cache = {}  # invalidate details cache
                if not user.check_nperms(nperms, nperm_type):
                    return view_func(*args, **kwd)
                else:
                    context = {'main': div()}
                    context['main'].add(
                        p(_("You don't have permissions for this page!")))
                    if fred.config.debug:
                        context['main'].add(
                            p('nperms=%s, nperm_type=%s' % (
                                nperms, nperm_type)))
                    return BaseSiteMenu(context).render()

            redir_addr = '/login/?next=%s' % get_current_url(cherrypy.request)
            raise cherrypy.HTTPRedirect(redir_addr)

        return _wrapper
    return _decorator


def check_onperm(objects_nperms, check_type='all'):
    def _decorator(view_func):
        def _wrapper(*args, **kwd):
            self = args[0]
            user = cherrypy.session.get('user', None)
            if user:
                utils.details_cache = {}  # invalidate details cache
                nperms = []
                if isinstance(objects_nperms, types.StringTypes):
                    onperms = [objects_nperms]
                else:
                    onperms = objects_nperms
                for objects_nperm in onperms:
                    nperms.append('%s.%s' % (objects_nperm, self.classname))
                if user.check_nperms(nperms, check_type):
                    context = {'message': div()}
                    context['message'].add(
                        p(_("You don't have permissions for this page!")))
                    if fred.config.debug:
                        context['message'].add(
                            p(
                                'usernperm = %s,' % user.nperms, br(),
                                'nperms=%s,' % nperms, br(),
                                'nperm_type=%s' % check_type, br()))
                        context['message'].add(p(
                            "a tohle to je udelano nejsofistikovanejsim "
                            "decoratorem"))
                    return self._render('error', context)
                return view_func(*args, **kwd)

            redir_addr = '/login/?next=%s' % get_current_url(cherrypy.request)
            raise cherrypy.HTTPRedirect(redir_addr)

        return _wrapper
    return _decorator
