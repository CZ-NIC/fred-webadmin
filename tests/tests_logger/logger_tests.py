import mox

from fred_webadmin import sessionlogger 
from fred_webadmin.sessionlogger import LoggingException
from fred_webadmin.corba import ccReg

from nose.tools import with_setup, raises


class TestLoggerCommon(object):

    def setup(self):
        """ Creates mock corba object. """
        self.corba_mock = mox.Mox()


    @with_setup(setup)
    def test_create_logger_for_session(self):
        """ Logger gets created OK when all's OK. """
        dao = self.corba_mock.CreateMockAnything()

        dao.CreateSession(ccReg.EN, "test_name").AndReturn(9)
        dao.GetServiceActions(sessionlogger.service_type_webadmin).AndReturn([(1, "a"), (2, "b")])

        dao.CreateSession(ccReg.EN, "test_name").AndReturn(9)
        dao.GetServiceActions(sessionlogger.service_type_webadmin).AndReturn([(1, "a"), (2, "b")])
        
        self.corba_mock.ReplayAll()

        logger = sessionlogger.SessionLogger()
        rc = logger.start_session("EN", "test_name", dao=dao)
        
        assert logger is not None
        assert rc == True
        
        logger = sessionlogger.SessionLogger(throws_exceptions=True)
        rc = logger.start_session("EN", "test_name", dao=dao)

        assert logger is not None
        assert rc == True

        self.corba_mock.VerifyAll()


    @with_setup(setup)
    def test_close_session(self):
        """ Session closed OK, when all's OK. """
        dao = self.corba_mock.CreateMockAnything()

        dao.CreateSession(ccReg.EN, "test_name").AndReturn(9)
        dao.GetServiceActions(sessionlogger.service_type_webadmin).AndReturn([(1, "a"), (2, "b")])
        dao.CloseSession(9).AndReturn(True)

        dao.CreateSession(ccReg.EN, "test_name").AndReturn(9)
        dao.GetServiceActions(sessionlogger.service_type_webadmin).AndReturn([(1, "a"), (2, "b")])
        dao.CloseSession(9).AndReturn(True)

        self.corba_mock.ReplayAll()

        logger = sessionlogger.SessionLogger()
        rc1 = logger.start_session(lang="EN", name="test_name", dao=dao)
        rc2 = logger.close_session()

        assert logger is not None
        assert rc1 == True
        assert rc2 == True
        
        logger = sessionlogger.SessionLogger(throws_exceptions=True)
        rc1 = logger.start_session(lang="EN", name="test_name", dao=dao)
        rc2 = logger.close_session()

        assert logger is not None
        assert rc1 == True
        assert rc2 == True
        
        self.corba_mock.VerifyAll()


    @with_setup(setup)
    def test_create_request(self):
        """ Request is created when all's OK. """
        dao = self.corba_mock.CreateMockAnything()

        dao.CreateSession(ccReg.EN, "test_name").AndReturn(9)
        dao.GetServiceActions(sessionlogger.service_type_webadmin).AndReturn([(1, "foo"), (100, "ClientLogin"), (3, "bar")])
        dao.CreateRequest("127.0.0.1", sessionlogger.service_type_webadmin, "<foo test='content bar foo'>foofoofoo</foo>", [], 100, 9).AndReturn(42)
        
        dao.CreateSession(ccReg.EN, "test_name").AndReturn(9)
        dao.GetServiceActions(sessionlogger.service_type_webadmin).AndReturn([(1, "foo"), (100, "ClientLogin"), (3, "bar")])
        dao.CreateRequest("127.0.0.1", sessionlogger.service_type_webadmin, "<foo test='content bar foo'>foofoofoo</foo>", [], 100, 9).AndReturn(42)

        self.corba_mock.ReplayAll()
        
        logger = sessionlogger.SessionLogger()
        rc = logger.start_session(lang="EN", name="test_name", dao=dao)
        request = logger.create_request("127.0.0.1", "<foo test='content bar foo'>foofoofoo</foo>", "ClientLogin")

        assert logger is not None
        assert rc == True
        assert request is not None

        logger = sessionlogger.SessionLogger(throws_exceptions=True)
        rc = logger.start_session(lang="EN", name="test_name", dao=dao)
        request = logger.create_request("127.0.0.1", "<foo test='content bar foo'>foofoofoo</foo>", "ClientLogin")

        assert logger is not None
        assert rc == True
        assert request is not None

        self.corba_mock.VerifyAll()



class TestLoggerNoExceptionsThrown(object):

    def setup(self):
        """ Creates mock corba object. """
        self.corba_mock = mox.Mox()


    @with_setup(setup)
    def test_create_logger_for_session_invalid_lang(self):
        """ Session does not start when invalid langauge is provided. """
        dao = self.corba_mock.CreateMockAnything()

        self.corba_mock.ReplayAll()

        logger = sessionlogger.SessionLogger(throws_exceptions=False)
        rc = logger.start_session("test_invalid_lang", "test_name", dao=dao)

        assert logger is not None
        assert rc == False

        self.corba_mock.VerifyAll()


    @with_setup(setup)
    def test_create_request_invalid_action_type(self):
        """ Request is NONE when invalid action type is provided. """
        dao = self.corba_mock.CreateMockAnything()

        dao.CreateSession(ccReg.EN, "test_name").AndReturn(9)
        dao.GetServiceActions(sessionlogger.service_type_webadmin).AndReturn([(1, "foo"), (100, "ClientLogin"), (3, "bar")])

        self.corba_mock.ReplayAll()

        logger = sessionlogger.SessionLogger()
        rc = logger.start_session(lang="EN", name="test_name", dao=dao)
        request = logger.create_request("127.0.0.1", "<foo test='content bar foo'>foofoofoo</foo>", "Invalid action type")

        assert logger is not None
        assert rc == True
        assert request is None

        self.corba_mock.VerifyAll()


    @with_setup(setup)
    def test_create_request_failed(self):
        """ Request is NONE when corba CreateRequest fails. """
        dao = self.corba_mock.CreateMockAnything()

        dao.CreateSession(ccReg.EN, "test_name").AndReturn(9)
        dao.GetServiceActions(sessionlogger.service_type_webadmin).AndReturn([(1, "foo"), (100, "ClientLogin"), (3, "bar")])
        dao.CreateRequest("127.0.0.1", sessionlogger.service_type_webadmin, "<foo test='content bar foo'>foofoofoo</foo>", [], 100, 9).AndReturn(0)

        self.corba_mock.ReplayAll()

        logger = sessionlogger.SessionLogger()
        rc1 = logger.start_session(lang="EN", name="test_name", dao=dao)
        request = logger.create_request("127.0.0.1", "<foo test='content bar foo'>foofoofoo</foo>", "ClientLogin")

        assert logger is not None
        assert rc1 == True
        assert request is None

        self.corba_mock.VerifyAll()


    @with_setup(setup)
    def test_close_session_failed(self):
        """ Session closed failed, when Corba CloseSession fails. """ 
        dao = self.corba_mock.CreateMockAnything()

        dao.CreateSession(ccReg.EN, "test_name").AndReturn(9)
        dao.GetServiceActions(sessionlogger.service_type_webadmin).AndReturn([(1, "a"), (2, "b")])
        dao.CloseSession(9).AndReturn(False)

        self.corba_mock.ReplayAll()

        logger = sessionlogger.SessionLogger()
        rc1 = logger.start_session(lang="EN", name="test_name", dao=dao)
        rc2 = logger.close_session()

        assert logger is not None
        assert rc1 == True
        assert rc2 == False

        self.corba_mock.VerifyAll()


class TestLogger_with_exceptions(object):

    def setup(self):
        """ Creates mock corba object. """
        self.corba_mock = mox.Mox()

    @with_setup(setup)
    @raises(LoggingException)
    def test_create_logger_for_session_invalid_lang(self):
        """ LoggingException thrown when invalid langauge is provided. """
        dao = self.corba_mock.CreateMockAnything()

        self.corba_mock.ReplayAll()

        logger = sessionlogger.SessionLogger(throws_exceptions=True)
        rc = logger.start_session("test_invalid_lang", "test_name", dao=dao)

        assert logger is not None
        assert rc == False

        self.corba_mock.VerifyAll()


    @with_setup(setup)
    @raises(LoggingException)
    def test_create_request_invalid_action_type(self):
        """ LoggingException thrown when invalid action type is provided. """
        dao = self.corba_mock.CreateMockAnything()

        dao.CreateSession(ccReg.EN, "test_name").AndReturn(9)
        dao.GetServiceActions(sessionlogger.service_type_webadmin).AndReturn([(1, "foo"), (100, "ClientLogin"), (3, "bar")])

        self.corba_mock.ReplayAll()

        logger = sessionlogger.SessionLogger(throws_exceptions=True)
        rc = logger.start_session(lang="EN", name="test_name", dao=dao)
        request = logger.create_request("127.0.0.1", "<foo test='content bar foo'>foofoofoo</foo>", "Invalid action type")

        assert logger is not None
        assert rc == True

        self.corba_mock.VerifyAll()


    @with_setup(setup)
    @raises(sessionlogger.LoggingException)
    def test_create_request_failed(self):
        """ LoggingException thrown when corba CreateRequest fails. """
        dao = self.corba_mock.CreateMockAnything()

        dao.CreateSession(ccReg.EN, "test_name").AndReturn(9)
        dao.GetServiceActions(sessionlogger.service_type_webadmin).AndReturn([(1, "foo"), (100, "ClientLogin"), (3, "bar")])
        dao.CreateRequest("127.0.0.1", sessionlogger.service_type_webadmin, "<foo test='content bar foo'>foofoofoo</foo>", [], 100, 9).AndReturn(0)

        self.corba_mock.ReplayAll()

        logger = sessionlogger.SessionLogger(throws_exceptions=True)
        rc1 = logger.start_session(lang="EN", name="test_name", dao=dao)
        request = logger.create_request("127.0.0.1", "<foo test='content bar foo'>foofoofoo</foo>", "ClientLogin")

        assert logger is not None
        assert rc1 == True

        self.corba_mock.VerifyAll()


    @with_setup(setup)
    @raises(sessionlogger.LoggingException)
    def test_close_session_failed(self):
        """ LoggingException thrown when Corba CloseSession fails. """ 
        dao = self.corba_mock.CreateMockAnything()

        dao.CreateSession(ccReg.EN, "test_name").AndReturn(9)
        dao.GetServiceActions(sessionlogger.service_type_webadmin).AndReturn([(1, "a"), (2, "b")])
        dao.CloseSession(9).AndReturn(False)

        self.corba_mock.ReplayAll()

        logger = sessionlogger.SessionLogger(throws_exceptions=True)
        rc = logger.start_session(lang="EN", name="test_name", dao=dao)
        rc = logger.close_session()

        assert logger is not None
        assert rc1 == True


        self.corba_mock.VerifyAll()


class TestLogRequest(object):
    def setup(self):
        """ Creates mock corba object. """
        self.corba_mock = mox.Mox()
        self.dao = self.corba_mock.CreateMockAnything()


    
    @with_setup(setup)
    def test_update_single_property(self):
        prop = ccReg.RequestProperty(name='test name', value='test value', output=False, child=False)
        self.dao.UpdateRequest(42, [mox.IsA(ccReg.RequestProperty)]).AndReturn(True)

        prop = ccReg.RequestProperty(name='test name', value='test value', output=False, child=False)
        self.dao.UpdateRequest(42, [mox.IsA(ccReg.RequestProperty)]).AndReturn(True)

        self.corba_mock.ReplayAll()
        
        request = sessionlogger.LogRequest(self.dao, 42)
        rc = request.update("test name", "test value", False, False)

        assert request is not None
        assert rc == True

        request = sessionlogger.LogRequest(self.dao, 42, True)
        rc = request.update("test name", "test value", False, False)

        assert request is not None
        assert rc == True

        self.corba_mock.VerifyAll()


    @raises(LoggingException)
    @with_setup(setup)
    def test_update_failed(self):
        self.dao.UpdateRequest(42, [mox.IsA(ccReg.RequestProperty)]).AndReturn(False)
        self.dao.UpdateRequest(42, [mox.IsA(ccReg.RequestProperty)]).AndReturn(False)

        self.corba_mock.ReplayAll()
        
        request = sessionlogger.LogRequest(self.dao, 42, False)
        rc = request.update("test name", "test value", False, False)

        assert request is not None
        assert rc == False

        request = sessionlogger.LogRequest(self.dao, 42, True)
        rc = request.update("test name", "test value", False, False)
        
        assert request is not None

        self.corba_mock.VerifyAll()


    @with_setup(setup)
    def test_commit(self):
        self.dao.CloseRequest(42, "<foo>bar</foo>", []).AndReturn(True)
        self.dao.CloseRequest(42, "<foo>bar</foo>", []).AndReturn(True)

        self.corba_mock.ReplayAll()

        request = sessionlogger.LogRequest(self.dao, 42)
        rc = request.commit("<foo>bar</foo>")

        assert request is not None
        assert rc == True
        
        request = sessionlogger.LogRequest(self.dao, 42)
        rc = request.commit("<foo>bar</foo>")

        assert request is not None
        assert rc == True

        self.corba_mock.VerifyAll()