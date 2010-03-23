#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    Logging framework.
"""

import traceback
import omniORB

import fred_webadmin.corbarecoder as recoder
import fred_webadmin.logger.dummylogger

from fred_webadmin.corba import ccReg

__all__ = ["SessionLogger", "LogRequest", 
            "LoggingException", "service_type_webadmin"]

# Constant representing web admin service type (hardcoded in db).
service_type_webadmin = 4

"""
*** Module initialization section. ***
"""

# Initialize (lowercase lang code string -> lang code int) mapping from
# corba IDL (e.g. {'cs' : ccReg.CS, 'en' : ccReg.EN}).
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
    """

    def __init__(self, dao):
        """Inits SessionLogger.

            Arguments:
                dao: Data Access Object for the logger. 
                    That's where we get our data from / send them to.
                    Generally it's a Corba Logger object for normal use and 
                    mock object for unit tests.

        """
        self.dao = dao
        self.actions = None 
        self.logging_session_id = None
        self.common_properties = {}

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
            name = recoder.u2c(name)

        try:
            lang_code = languages[lang.lower()]
        except KeyError:
            raise ValueError("Invalid language provided to SessionLogger.")
        
        self.logging_session_id = self.dao.CreateSession(lang_code, name)
        if self.logging_session_id == 0:
            raise LoggingException(
                """Logging session failed to start with args: (%s, %s).""" %
                (lang_code, name))
        self._load_action_codes(service_type)

    def set_common_property(self, name, value, output=False, child=False):
        """Set a property that will automatically be logged in every request.
            
            Common properties are logged when a log request is created.
            Therefore if you create a request and then set a common property, it
            will be logged automatically in every following request, but not
            this one.

            Arguments:
                See LogRequest.update.
        """
        name = recoder.u2c(name)
        self.common_properties[name] = (name, value, output, child)

    def create_request(self, source_ip, content, action_type, properties=None):
        """
            Creates a request object on the server.
            Returns a new LogRequest object or None on error.
        """
        properties = properties or []
        request_id = self._server_create_request(
            source_ip, content, action_type, properties)
        log_request = LogRequest(self.dao, request_id)
        log_request.update_multiple(self.common_properties.values())
        return log_request

    def close_session(self):
        """ 
            Tells the server to close this logging session.
            Returns True iff session closed successfully.
        """
        ret_code = self.dao.CloseSession(self.logging_session_id)
        if ret_code == 0:
            raise LoggingException("CloseSession failed.")

    def _load_action_codes(self, service_type):
        """
            Request (action string code -> action int code) mapping from
            the server. 
        """
        action_list = self.dao.GetServiceActions(service_type)
        self.actions = {}
        for action in action_list:
            self.actions[action.status] = action.id

    def _server_create_request(self, source_ip, content, action_type, 
                                properties):
        """
            Ask the server to create a new logging request.
            Returns request id iff request has been created successfully.
        """
        if content is None:
            content = ""
        try:
            action = self.actions[action_type]
        except KeyError:
            raise ValueError(
                "Invalid action type %s. Original exception: %s." %
                (action_type, traceback.format_exc()))

        request_id = self.dao.CreateRequest(
            source_ip, service_type_webadmin, content, properties, 
            action, self.logging_session_id)
        if request_id == 0:
            raise LoggingException(
                "Failed to create a request with args: (%s, %s, %s, %s)." % 
                (source_ip, content, action_type, properties))
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

    def __init__(self, dao, request_id):
        self.dao = dao
        self.request_id = request_id

    def _convert_nested_to_str(self, value):
        """ Converts nested lists (or tuples) of objects to nested lists of
            strings. """
        if not isinstance(value, list) and not isinstance(value, tuple):
            return str(value)
        return [self._convert_nested_to_str(item) for item in value]

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
            value = str(self._convert_nested_to_str(value))
        name = recoder.u2c(name)
        value = recoder.u2c(value)
        prop = [ccReg.RequestProperty(name, value, output, child)]
        success = self.dao.UpdateRequest(self.request_id, prop)
        if not success:
            raise LoggingException(
                "UpdateRequest failed with args: (%s, %s)." % 
                (self.request_id, property))

    def update_multiple(self, properties):
        """
            Add multiple rows to the log request.
            
            Note: Must be called when I want to use a child property. Calling
            LogRequest.update(...) erases the child/parent information.

            Arguments:
                properties: List of (name, value, output, child) tuples. See
                LogRequest.update.
        """
        prop_list = (properties if isinstance(properties, list) else
            [properties])

        props = []
        for name, value, output, child in prop_list:
            if not isinstance(name, basestring):
                name = str(name)
            if not isinstance(value, basestring):
                value = str(self._convert_nested_to_str(value))
            name = recoder.u2c(name)
            value = recoder.u2c(value)
            props.append(ccReg.RequestProperty(name, value, output, child))

        success = self.dao.UpdateRequest(self.request_id, props)
        if not success:
            raise LoggingException(
                "UpdateRequest failed with args: (%s, %s)." % 
                (self.request_id, props))

    def commit(self, content=""):
        """ Close this logging request. Warning: the request cannot be changed
            anymore after committing. """
        success = self.dao.CloseRequest(self.request_id, content, [])
        if not success:
            raise LoggingException("CloseRequest failed.")


class SessionLoggerFailSilent(SessionLogger):
    """ SessionLogger that does not raise exceptions on failure. 
    """
    def __init__(self, *args, **kwargs):
        SessionLogger.__init__(self, *args, **kwargs)

    def start_session(self, *args, **kwargs):
        try:
            SessionLogger.start_session(self, *args, **kwargs)
        except LoggingException:
            pass
        except omniORB.CORBA.SystemException:
            #TODO: Re-think somehow?
            # I have to reraise it, so that I know in ADIF.login that I should
            # hide away the logger...
            raise
        except Exception:
            pass

    def set_common_property(self, *args, **kwargs):
        try:
            SessionLogger.set_common_property(self, *args, **kwargs)
        except Exception:
            pass

    def create_request(self, source_ip, content, action_type, properties=None):
        try:
            properties = properties or []
            request_id = self._server_create_request(
                source_ip, content, action_type, properties)
            log_request = LogRequestFailSilent(self.dao, request_id)
            log_request.update_multiple(self.common_properties.values())
            return log_request
        except Exception:
            return fred_webadmin.logger.dummylogger.DummyLogRequest()

    def close_session(self, *args, **kwargs): 
        try:
            SessionLogger.close_session(self, *args, **kwargs)
        except Exception:
            pass


class LogRequestFailSilent(LogRequest):
    """ LogRequest that does not raise exceptions on failure (to be used with
        SessionLoggerFailSilent). """
    def __init__(self, *args, **kwargs):
        LogRequest.__init__(self, *args, **kwargs)

    def update(self, *args, **kwargs):
        try:
            LogRequest.update(self, *args, **kwargs)
        except Exception:
            pass

    def update_multiple(self, *args, **kwargs):
        try:
            LogRequest.update_multiple(self, *args, **kwargs)
        except Exception:
            pass

    def commit(self, *args, **kwargs):
        try:
            LogRequest.commit(self, *args, **kwargs)
        except Exception:
            pass


class LoggingException(Exception):
    """ Generic exception thrown by this logging framework. """
    def __init__(self, value):
        Exception.__init__(self, value)
        self.value = value

    def __str__(self):
        return repr(self.value)
