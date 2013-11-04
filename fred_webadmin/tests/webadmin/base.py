from StringIO import StringIO

import cherrypy
import nose
import twill

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


class DaphneTestCase(object):
    """ Serves as a base class for testing Daphne controller layer (that's
        basically adif).
        Takes care of mocking admin, session and user CORBA objects. Also
        monkey patches the dynamically created cherrypy.session dict.
        Uses DummyLogger, so that we do not have to care about audit logging
        (that's SessionLogger).
    """
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

    def setUp(self):
        self.monkey_patch(
            fred_webadmin.user, 'auth_user', fred_webadmin.perms.dummy)
        self.web_session_mock = {}
        self.web_session_mock['Logger'] = logger.DummyLogger()

        self.monkey_patch(cherrypy, 'session', self.web_session_mock)
        self.monkey_patch(fred_webadmin, 'config', test_config)
        self.monkey_patch(fred_webadmin.utils, 'get_logger', logger.DummyLogger)

        cherrypy.config.update({"environment": "embedded"})


twill_output = StringIO()


@nose.tools.nottest
def init_test_server():
    root = fred_webadmin.controller.adif.prepare_root()
    wsgiApp = cherrypy.tree.mount(root)
    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                             'server.socket_port': 8080,
                           })
    cherrypy.server.start()
    # Redirect HTTP requests.
    twill.add_wsgi_intercept('localhost', 8080, lambda : wsgiApp)
    # Keep Twill quiet (suppress normal Twill output).
    twill.set_output(twill_output)


@nose.tools.nottest
def deinit_test_server():
    # Remove the intercept.
    twill.remove_wsgi_intercept('localhost', 8080)
    # Shut down Cherrypy server.
    cherrypy.server.stop()
