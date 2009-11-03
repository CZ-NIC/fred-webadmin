#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    Logging framework.
"""

import omniORB
import logging
import traceback

from fred_webadmin.corba import ccReg
from fred_webadmin.utils import u2c

__all__ = ["SessionLogger", "LogRequest", 
            "LoggingException", "service_type_webadmin"]

# Constant representing web admin service type (hardcoded in db).
service_type_webadmin = 4

"""
*** Module initialization section. ***
"""

# Initilize (lowercase lang code string -> lang code int) mapping from
# corba IDL (e.g. {cs : ccReg.CS, en : ccReg.EN}).
languages = dict((code._n.lower(), code) for code in ccReg.Languages._items)


"""
*** Class definitions ***
"""

class SessionLogger(object):
    """ 
    Logger for a session.

    Example usage:
        logger = SessionLogger()
        logger.start_session("CS", "user name")
        req = logger.create_request("127.0.0.1", "<foo/>", "NSSetSUpdate")
        req.update("logging_session_id", "321687468486111")
        ...
        req.commit("<foo/>")
        logger.close_session()

    Attributes:
        actions: Dictionary containing (string action type -> action id integer)
            mapping.
        logging_session_id: Integer id of the logging session.
        dao: Data Access Object. That's where we get our data from / send them 
            to.
        common_properties: List of properties that should be added by default
            to every log request.
        throws_exceptions: Boolean indicating whether SessionLogger should
            throw Exceptions or return error codes on error.
        log: When we encounter an error, this function is called with a string
            description of what happened.

    """

    def __init__(self, dao, throws_exceptions=False, logging_function=None):
        """Inits SessionLogger.

            Arguments:
                
        """
        self.dao = dao
        self.actions = None 
        self.logging_session_id = None
        self.common_properties = {}
        self.throws_exceptions = throws_exceptions
        self.log = logging_function or logging.debug

    def start_session(self, lang, name, service_type=4):
        """Starts a new logging session.

            Arguments:
                lang: String. Language of the started session.
                name: String. Registrar ID for EPP session or user name for
                    WebAdmin.
                service_type: Integer. Type of service that is going to be
                    logged.
                dao: Data Access Object for logging. Probably Corba Logger
                    object for normal usage.
            
            Returns: True if session started successfully, False otherwise.

            Raises: If SessionLogger should throw exceptions, throws
                LoggingException on error.

        """
        if not isinstance(name, basestring):
            name = str(name)
        else:
            name = u2c(name)
        try:
            if languages.has_key(lang.lower()) == False:
                raise ValueError("Invalid language provided to SessionLogger.")
            else:
                lang_code = languages[lang.lower()]
            
            self.logging_session_id = self.dao.CreateSession(lang_code, 
                                                                 name)
            if self.logging_session_id == 0:
                raise LoggingException("""Invalid arguments provided to
                                        CreateSession: (%s, %s).""" %
                                        (lang_code, name))
            self.__load_action_codes(service_type)

            return True
        except Exception, exc:
            self.log(traceback.format_exc())
            if self.throws_exceptions:
                raise LoggingException(exc)
            else:
                return False

    def set_common_property(self, name, value, output=False, child=False):
        """Set a property that will automatically be logged in every request.
            
            Common properties are logged when a log request is created.
            Therefore if you create a request and then set a common property, it
            will be logged automaticalyy in every following request, but not
            this one.

            Arguments:
                See LogRequest.update.
        """
        name = u2c(name)
        self.common_properties[name] = (name, value, output, child)

    def create_request(self, source_ip, content, action_type, properties=None):
        """
            Creates a request object on the server.
            Returns a new LogRequest object or None on error.
        """
        properties = properties or []
        try:
            request_id = self.__server_create_request(source_ip, content, 
                                                      action_type, properties)
        except Exception, e:
            self.log(traceback.format_exc())
            if self.throws_exceptions:
                raise LoggingException(e)
            request_id = -1

        log_request = LogRequest(self.dao, request_id, 
                                 throws_exceptions=self.throws_exceptions,
                                 logging_function=self.log) 
        try:
            log_request.update_multiple(self.common_properties.values())
            return log_request
        except Exception, exc:
            self.log(traceback.format_exc())
            if self.throws_exceptions:
                raise LoggingException(exc)
        return log_request

    def create_request_login(self, source_ip, content, action_type, 
                             properties=None):
        """
            Creates a login request object on the server.
            Returns a new LogRequestLogin or None on error.
        """
        properties = properties or []
        try:
            request_id = self.__server_create_request(source_ip, content, 
                                                      action_type, properties)
        except Exception, e:
            self.log(traceback.format_exc())
            if self.throws_exceptions:
                raise LoggingException(e)
            request_id = -1
        # TODO(tomas): Cannot send logging_session_id now, otherwise the
        # call fails. When it's a login log request, the logging_session_id
        # must only be sent when closing the request.
        log_request = LogRequestLogin(
            self.dao, request_id, self.logging_session_id, 
            throws_exceptions=self.throws_exceptions,
            logging_function=self.log) 
        try:
            log_request.update_multiple(self.common_properties.values())
            return log_request
        except Exception, e:
            self.log(traceback.format_exc())
            if self.throws_exceptions:
                raise LoggingException(e)
            # When throws_exceptions == False, we always need to return a
            # LogRequest object. That's the whole point of not having silent 
            # errors: user can ignore them. If this returned None, we could call
            # None.update_request and still would get an Exception in the outer
            # code.
            return log_request

    def close_session(self):
        """ 
            Tells the server to close this logging session.
            Returns True iff session closed successfully.
        """
        try:
            ret_code = self.dao.CloseSession(self.logging_session_id)
            if ret_code == 0:
                raise LoggingException("CloseSession failed.")
            return True
        except Exception, exc:
            self.log(traceback.format_exc())
            if self.throws_exceptions:
                raise LoggingException(exc)
            else:
                return False

    def __load_action_codes(self, service_type):
        """
            Request (action string code -> action int code) mapping from
            the server. 
        """
        action_list = self.dao.GetServiceActions(service_type)
        self.actions = {}
        for action in action_list:
            self.actions[action.status] = action.id

    def __server_create_request(self, source_ip, content, action_type, 
                                properties):
        """
            Ask the server to create a new logging request.
            Returns request id iff request has been created successfully.
        """
        if content is None:
            content = ""
        if not self.actions.has_key(action_type):
            raise ValueError("Invalid action type: %s." % action_type)
        try:
            request_id = self.dao.CreateRequest(source_ip, 
                                                service_type_webadmin,
                                                content, 
                                                properties, 
                                                self.actions[action_type],
                                                self.logging_session_id)
        except omniORB.CORBA.BAD_PARAM, e:
            raise LoggingException("""CreateRequest failed with args: %s, %s, 
                                    %s, %s, %s, %s. Original exception: %s""" % 
                                    (source_ip, service_type_webadmin, content, 
                                    properties, self.actions[action_type], 
                                    self.logging_session_id, str(e)))
        if request_id == 0:
            raise LoggingException("CreateRequest failed.")

        return request_id


class LogRequest(object):
    """ 
        A request for logging. Use one LogRequest object for one action to be 
        logged and use the update method to log the necessary information for 
        this action.

        Should NOT be instantiated directly; use SessionLogger.create_request.

        Example usage: 
            req = session_logger.create_request(...)
            req.update("session_id", 132)
            ...
            req.commit("<foo/>")

        Arguments:
            dao: Data Access Object for logging. Usually Corba Logger object.
            request_id: Integer identifier of the request.
            throws_exceptions: Boolean. True iff SessionLogger throws 
                exceptions.
            log: When we encounter an error, this function is called with 
                a string description of what happened.
    """

    def __init__(self, dao, request_id, throws_exceptions, logging_function):
        self.dao = dao
        self.request_id = request_id
        self.throws_exceptions = throws_exceptions
        self.log = logging_function

    def update(self, name, value, output=False, child=False):
        """
            Add a new row to the log request.

            Arguments:
                name: Name of the property to be logged. Should be an ascii
                    string, otherwise it is converted to ascii.
                value: Value of the property to be logged. Should be an ascii
                    string, otherwise it is converted to ascii.
                output: Bool indicating whether the log property has any output
                    associated with it.
                child: Bool flag. Setting the child flag to true means this
                    record is a child property of the most recent record (in the
                    same sequence) which isn't a child.

            Returns:
                True if request was logged OK, False otherwise.
            Raises:
                LoggingException: If SessionLogger.throws_exceptions 
                is True and any error has occured.
        """

        if not isinstance(name, basestring):
            name = str(name)
        if not isinstance(value, basestring):
            value = str(value)
        name = u2c(name)
        value = u2c(value)
        try:
            prop = [ccReg.RequestProperty(name, value, output, child)]
            success = self.dao.UpdateRequest(self.request_id, prop)
            if not success:
                raise LoggingException("UpdateRequest failed with args: %s,"
                                       "%s." % self.request_id, property)
            return True
        except Exception, exc:
            self.log(traceback.format_exc())
            if self.throws_exceptions:
                raise LoggingException(exc)
            else:
                return False

    def update_multiple(self, properties):
        """
            Add multiple rows to the log request.

            Arguments:
                properties: List of (name, value, output, child) tuples. See
                LogRequest.update.
        """
        prop_list = (properties if isinstance(properties, list) else
            [properties])
        for (name, value, output, child) in prop_list:
            self.update(name, value, output, child)

    def commit(self, content=""):
        """ Close this logging request. Warning: the request cannot be changed
            anymore after committing. """
        try:
            success = self.dao.CloseRequest(self.request_id, content, [])
            if not success:
                raise LoggingException("CloseRequest failed.")
            return True
        except Exception, exc:
            self.log(traceback.format_exc())
            if self.throws_exceptions:
                raise LoggingException(exc)
            else:
                return False


class LogRequestLogin(LogRequest):
    """ 
        A request for logging a login action.
        See LogRequest class for further information.
        Should NOT be instantiated directly; use 
        SessionLogger.create_request_login.
    """
    def __init__(self, dao, request_id, logging_session_id, throws_exceptions, 
                 logging_function):
        LogRequest.__init__(self, dao, request_id, throws_exceptions, 
                            logging_function)
        self.logging_session_id = logging_session_id

    def commit(self, content=""):
        try:
            success = self.dao.CloseRequestLogin(self.request_id, content, [], 
                                            self.logging_session_id)
            if not success:
                raise LoggingException("""CloseRequest failed with args: (%s, 
                                        %s, %s, %s).""" % (self.request_id, 
                                        content, [], self.logging_session_id))
            return True
        except Exception, e:
            self.log(traceback.format_exc())
            if self.throws_exceptions:
                raise LoggingException(e)
            else:
                return False


class LoggingException(Exception):
    """ Generic exception thrown by this logging framework. """
    def __init__(self, value):
        Exception.__init__(self, value)
        self.value = value

    def __str__(self):
        return repr(self.value)
