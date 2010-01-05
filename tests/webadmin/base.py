import mox
import cherrypy
import fred_webadmin as webadmin
import fred_webadmin.user as user
import fred_webadmin.logger.dummylogger as logger
from fred_webadmin import setuplog

setuplog.setup_log()

test_config = webadmin.config
test_config.cherrycfg['global']['server.socket_port'] = 8081

class DaphneTestCase(object):
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
        self.corba_mock = mox.Mox()
        self.corba_session_mock = self.corba_mock.CreateMockAnything()

        self.corba_user_mock = self.corba_mock.CreateMockAnything()
        self.corba_user_mock.__str__ = lambda : "corba user mock"

        self.admin_mock = self.corba_mock.CreateMockAnything()
        self.admin_mock.__str__ = lambda : "admin mock"
        
        self.web_session_mock = {}
        self.web_session_mock['user'] = user.User(self.corba_user_mock)
        self.web_session_mock['Logger'] = logger.DummyLogger()
        self.web_session_mock['Admin'] = self.admin_mock

        self._on_teardown = []
        self.monkey_patch(
            webadmin.utils, 'get_corba_session',  
            lambda : self.corba_session_mock)
        self.monkey_patch(cherrypy, 'session', self.web_session_mock)
        self.monkey_patch(webadmin, 'config', test_config)


