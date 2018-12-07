#
# Copyright (C) 2010-2018  CZ.NIC, z. s. p. o.
#
# This file is part of FRED.
#
# FRED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FRED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FRED.  If not, see <https://www.gnu.org/licenses/>.

from functools import wraps
from StringIO import StringIO

import cherrypy
import nose
import twill
from wsgi_intercept import add_wsgi_intercept, requests_intercept, remove_wsgi_intercept

import fred_webadmin.config
import fred_webadmin.controller.adif

test_config = fred_webadmin.config
# Disable logging by default. It pollutes the tests. Use DummyLogger.
test_config.audit_log['logging_actions_enabled'] = False
test_config.cherrycfg['global']['server.socket_port'] = 8081
# Disable permissions checking by default. It pollutes the tests.
# If a test wants to check permissions, it should enable it for itself only.
test_config.permissions['enable_checking'] = False
test_config.cherrycfg['environment'] = 'embedded'
test_config.iors = (('test', 'localhost_test', 'fredtest'),)

import pylogger.dummylogger as logger
import fred_webadmin.perms.dummy
import fred_webadmin.utils


class DaphneBaseTestCase(object):
    def __init__(self):
        self._on_teardown = []

    def monkey_patch(self, obj, attr, new_value):
        """ Taken from
            http://lackingrhoticity.blogspot.com/2008/12/
            helper-for-monkey-patching-in-tests.html

            Basically it stores the original object before monkeypatching and
            then restores it at teardown. Which is handy, because we do not
            want the object to stay monkeypatched between unit tests (if the
            test needs to do the patch, it can, but it should not change the
            environment for the other tests.
        """
        try:
            old_value = getattr(obj, attr)
        except AttributeError:
            def tear_down():
                delattr(obj, attr)
        else:
            def tear_down():
                setattr(obj, attr, old_value)
        self._on_teardown.append(tear_down)
        setattr(obj, attr, new_value)

    def tearDown(self):
        """ Taken from
            http://lackingrhoticity.blogspot.com/2008/12/
            helper-for-monkey-patching-in-tests.html"""
        for func in reversed(self._on_teardown):
            func()


class DaphneTestCase(DaphneBaseTestCase):
    """ Serves as a base class for testing Daphne controller layer (that's
        basically adif).
        Takes care of mocking admin, session and user CORBA objects. Also
        monkey patches the dynamically created cherrypy.session dict.
        Uses DummyLogger, so that we do not have to care about audit logging
        (that's SessionLogger).
    """

    def setUp(self):
        self.monkey_patch(
            fred_webadmin.user, 'auth_user', fred_webadmin.perms.dummy)
        self.web_session_mock = {}

        self.monkey_patch(cherrypy, 'session', self.web_session_mock)
        self.monkey_patch(fred_webadmin, 'config', test_config)
        self.monkey_patch(fred_webadmin.utils, 'get_logger', logger.DummyLogger)

        cherrypy.config.update({"environment": "embedded"})


twill_output = StringIO()


@nose.tools.nottest
def init_test_server():
    requests_intercept.install()
    root = fred_webadmin.controller.adif.prepare_root()
    wsgiApp = cherrypy.tree.mount(root)
    # Redirect HTTP requests.
    add_wsgi_intercept('localhost', 8080, lambda: wsgiApp)


@nose.tools.nottest
def deinit_test_server():
    # Remove the intercept.
    remove_wsgi_intercept('localhost', 8080)
    requests_intercept.uninstall()


def enable_corba_comparison(corba_type):
    def corba_eq(self, other):
        if not isinstance(other, self.__class__):
            return False
        import omniORB
        corba_type_desc = omniORB.findType(self._NP_RepositoryId)
        for i in range(4, len(corba_type_desc), 2):
            attr_name = corba_type_desc[i]
            if getattr(self, attr_name, None) != getattr(other, attr_name, None):
                return False
        return True

    def corba_not_eq(self, other):
        return not self.__eq__(other)

    corba_type.__eq__ = corba_eq
    corba_type.__ne__ = corba_not_eq


def revert_to_default_corba_comparison(corba_type):
    delattr(corba_type, '__eq__')
    delattr(corba_type, '__ne__')


def enable_corba_comparison_decorator(corba_type):
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            enable_corba_comparison(corba_type)
            try:
                retval = func(*args, **kwargs)
            finally:
                revert_to_default_corba_comparison(corba_type)
            return retval
        return wrapped
    return wrapper


class TestAuthorizer(object):
    """ Implements the authorizer interface and allows every action.
        To be used when permission checking is disabled.
    """
    def __init__(self, username='testUser', test_perms=None):
        self._username = username
        if test_perms is None:
            self._perms = []
        else:
            self._perms = test_perms

    def has_permission(self, obj, action):
        return '{}.{}'.format(action, obj) in self._perms

    def add_perms(self, *perms):
        for perm in perms:
            self._perms.append(perm)

    def rem_perms(self, *perms):
        for perm in perms:
            if perm in self._perms:
                self._perms.remove(perm)

    def has_permission_detailed(self, obj, action, obj_id):
        return True

    def check_detailed_present(self, obj, action):
        return False

    def has_field_permission(self, obj, action, field_name):
        return True
