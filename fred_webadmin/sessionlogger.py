#!/usr/bin/python
# -*- coding: utf-8 -*-
import omniORB
import logging
import traceback

from fred_webadmin import corba
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
        should_throw_exceptions: Boolean indicating whether SessionLogger should
            throw Exceptions or return error codes on error.
        log: When should_throw_exceptions == True and we encounter an error,
            this function is called with a string description of what happened.

    """

    def __init__(self, throws_exceptions=False, logging_function=None):
        """ 
            Initializes all values and starts a logging session on the server.
            When @throws_exceptions is True, logger throws LoggingException
            if any error occurrs.
        """
        self.actions = None 
        self.logging_session_id = None
        self.dao = None # Data Access Object
        self.common_properties = {}
        self.should_throw_exceptions = throws_exceptions
        self.log = logging_function or logging.debug    # Function for logging

    def start_session(self, lang, name, service_type=4, dao=None):
        """
            Starts a new logging session. Returns true iff session started
            successfully.
        """
        name = u2c(name)
        try:
            if dao is None:
                self.dao = corba.getObject('Logger', 'Logger')
            else:
                self.dao = dao
                
            if languages.has_key(lang.lower()) == False:
                raise ValueError("Invalid language provided to SessionLogger.")
            else:
                lang_code = languages[lang.lower()]

            self.logging_session_id = self.dao.CreateSession(lang_code, 
                                                                 name)
            if self.logging_session_id == 0:
                raise LoggingException("""Invalid arguments provided to
                                        CreateSession: %s, %s.""" %
                                        (lang_code, name))

            self.__load_action_codes(service_type)

            return True
        except Exception as e:
            if self.should_throw_exceptions:
                self.log(str(e))
                self.log(traceback.format_exc())
                raise LoggingException(e)
            else:
                self.log(str(e))
                return False

    def set_common_property(self, name, value, output=False, child=False):
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
            log_request = LogRequest(self.dao, request_id, 
                                throws_exceptions=self.should_throw_exceptions,
                                logging_function=self.log) 
            log_request.update_multiple(self.common_properties.values())
            return log_request
        except Exception as e:
            if self.should_throw_exceptions:
                raise LoggingException(e)
            else:
                self.log(str(e))
                return None

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
            log_request = LogRequestLogin(self.dao, request_id, 
                                self.logging_session_id, 
                                throws_exceptions=self.should_throw_exceptions,
                                logging_function=self.log) 
            log_request.update_multiple(self.common_properties.values())
            return log_request
        except Exception as e:
            if self.should_throw_exceptions:
                raise LoggingException(e)
            else:
                self.log(str(e))
                return None

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
        except Exception as e:
            if self.should_throw_exceptions:
                raise LoggingException(e)
            else:
                self.log(str(e))
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
        if not self.actions.has_key(action_type):
            raise ValueError("""Invalid action type provided to CreateRequest: 
                              %s.""" % (action_type,))
        if content is None:
            content = ""
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
    """

    def __init__(self, dao, request_id, throws_exceptions, logging_function):
        self.dao = dao
        self.request_id = request_id
        self.should_throw_exceptions = throws_exceptions
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
                LoggingException: If SessionLogger.should_throw_exceptions 
                is True and any error has occured.
        """

        if not isinstance(name, basestring):
            name = str(name)
        if not isinstance(value, basestring):
            value = str(value)
        name = u2c(name)
        value = u2c(value)
        try:
            rc = self.dao.UpdateRequest(self.request_id, 
                                        [ccReg.RequestProperty(name, value, 
                                                               output, child)])
            if not rc:
                raise LoggingException("UpdateSession failed.")
            return True
        except Exception, e:
            if self.should_throw_exceptions:
                raise LoggingException(e)
            else:
                self.log(str(e))
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
            rc = self.dao.CloseRequest(self.request_id, content, [])
            if not rc:
                raise LoggingException("CloseRequest failed.")
            return True
        except Exception, e:
            if self.should_throw_exceptions:
                raise LoggingException(e)
            else:
                self.log(str(e))
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
            rc = self.dao.CloseRequestLogin(self.request_id, content, [], 
                                            self.logging_session_id)
            if not rc:
                raise LoggingException("""CloseRequest failed with args: (%s, 
                                        %s, %s, %s).""" % (self.request_id, 
                                        content, [], self.logging_session_id))
            return True
        except Exception as e:
            if self.should_throw_exceptions:
                raise LoggingException(e)
            else:
                self.log(str(e))
                return False


class LoggingException(Exception):
    """ Generic exception thrown by this logging framework when something
        goes wrong. """
    def __init__(self, value):
        Exception.__init__(self, value)
        self.value = value

    def __str__(self):
        return repr(self.value)
