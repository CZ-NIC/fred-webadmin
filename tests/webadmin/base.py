import mox
import cherrypy
import fred_webadmin as webadmin
import fred_webadmin.user as user
import fred_webadmin.logger.dummylogger as logger
import fred_webadmin.perms.dummy
from fred_webadmin.corba import Registry, ccReg

test_config = webadmin.config
test_config.audit_log['logging_actions_enabled'] = False
test_config.cherrycfg['global']['server.socket_port'] = 8081
test_config.cherrycfg['environment'] = 'embedded'
test_config.iors = (
    #(label, nshost, nscontext),
    ('test', 'localhost_test', 'fredtest'),)


class DaphneTestCase(object):
    """ Serves as a base class for testing Daphne controller layer (that's
        basically adif).
        Takes care of mocking admin, session and user corba objects. Also
        monkey patches the dymamically created cherrypy.session dict.
        Uses DummyLogger, so that we do not have to care about audit logging
        (that's SessionLogger).
    """
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
        self.corba_mock.UnsetStubs()
        self.corba_mock.ResetAll()
        
    def setUp(self, ldap=True):
        self._on_teardown = []

        self.corba_mock = mox.Mox()
        self.corba_conn_mock = self.corba_mock.CreateMockAnything()
        self.corba_session_mock = self.corba_mock.CreateMockAnything()
        self.corba_session_mock.__str__ = lambda : "corba session mock"

        self.corba_user_mock = self.corba_mock.CreateMockAnything()
        self.corba_user_mock.__str__ = lambda : "corba user mock"

#        self.admin_mock = self.corba_mock.CreateMockAnything()
#        self.admin_mock.__str__ = lambda : "admin mock"
        
        self.ldap_mock = self.corba_mock.CreateMockAnything()
        self.ldap_mock.__str__ = lambda : "ldap backend mock"

        self.authorizer_mock = self.corba_mock.CreateMockAnything()
        self.authorizer_mock.__str__ = lambda : "authorizer mock"

        self.monkey_patch(
            webadmin.user, 'auth_user', webadmin.perms.dummy)
        self.web_session_mock = {}
#        self.web_session_mock['user'] = user.User(self.corba_user_mock)
        self.web_session_mock['Logger'] = logger.DummyLogger()
#        self.web_session_mock['Admin'] = self.admin_mock
#        self.admin_mock =  AdminMock(self.corba_mock)
#        self.web_session_mock['Admin'] = self.admin_mock

#        self.monkey_patch(
#            webadmin.utils, 'get_corba_session',  
#            lambda : self.corba_session_mock)
        self.monkey_patch(cherrypy, 'session', self.web_session_mock)
        self.monkey_patch(webadmin, 'config', test_config)
#        self.monkey_patch(
#            webadmin.controller.adif, 'corba_obj', self.corba_conn_mock)

        cherrypy.config.update({ "environment": "embedded" })

