#!/usr/bin/python
# -*- coding: utf-8 -*-
import omniORB

from fred_webadmin import corba
from fred_webadmin.corba import ccReg
from logging import debug, error

__all__ = ["SessionLogger", "LogRequest", "LoggingException", "service_type_webadmin"]

"""
Handles logging of all the events that happen in fred_webadmin.
Is passed around in the cherrypy session object.
Uses the _Logger.idl interface.

id  - status
100 - ClientLogin
101 - ClientLogout
120 - PollAcknowledgement
121 - PollResponse
200 - ContactCheck
201 - ContactInfo
202 - ContactDelete
203 - ContactUpdate
204 - ContactCreate
205 - ContactTransfer
400 - NSsetCheck
401 - NSsetInfo
402 - NSsetDelete
403 - NSsetUpdate
404 - NSsetCreate
405 - NSsetTransfer
500 - DomainCheck
501 - DomainInfo
502 - DomainDelete
503 - DomainUpdate
504 - DomainCreate
505 - DomainTransfer
506 - DomainRenew
507 - DomainTrade
600 - KeysetCheck
601 - KeysetInfo
602 - KeysetDelete
603 - KeysetUpdate
604 - KeysetCreate
605 - KeysetTransfer
1000 - UnknownAction
1002 - ListContact
1004 - ListNSset
1005 - ListDomain
1006 - ListKeySet
1010 - ClientCredit
1012 - nssetTest
1101 - ContactSendAuthInfo
1102 - NSSetSendAuthInfo
1103 - DomainSendAuthInfo
1104 - Info
1106 - KeySetSendAuthInfo
1200 - InfoListContacts
1201 - InfoListDomains
1202 - InfoListNssets
1203 - InfoListKeysets
1204 - InfoDomainsByNsset
1205 - InfoDomainsByKeyset
1206 - InfoDomainsByContact
1207 - InfoNssetsByContact
1208 - InfoNssetsByNs
1209 - InfoKeysetsByContact
1210 - InfoGetResults


1300 - Login
1301 - Logout 
1302 - DomainFilter
1303 - ContactFilter
1304 - NSSetFilter
1305 - KeySetFilter
1306 - RegistrarFilter
1307 - InvoiceFilter
1308 - EmailsFilter
1309 - FileFilter
1310 - ActionsFilter
1311 - PublicRequestFilter 

1312 - DomainDetail
1313 - ContactDetail
1314 - NSSetDetail
1315 - KeySetDetail
1316 - RegistrarDetail
1317 - InvoiceDetail
1318 - EmailsDetail
1319 - FileDetail
1320 - ActionsDetail
1321 - PublicRequestDetail 

1322 - RegistrarCreate
1323 - RegistrarUpdate 

1324 - PublicRequestAccept
1325 - PublicRequestInvalidate 

1326 - DomainDig
1327 - FilterCreate 


1400 -  Login 
1401 -  Logout

1402 -  DisplaySummary
1403 -  InvoiceList
1404 -  DomainList
1405 -  FileDetail';

"""

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
        req.update("session_id", "321687468486111")
        ...
        req.commit("<foo/>")
        logger.close_session()

    """

    def __init__(self, throws_exceptions=False):
        """ 
            Initializes all values and starts a logging session on the server.
            When @throws_exceptions is True, logger throws LoggingException
            if any error occurrs.
        """
        self.request_id = 0
        self.actions = None 
        self.session_id = 0
        self.dao = None
        self.should_throw_exceptions = throws_exceptions


    def start_session(self, lang, name, service_type=4, dao=None):
        """
            Starts a new logging session. Returns true iff session started
            successfully.
        """
        try:
            self.service_type = service_type

            if dao is None:
                self.dao = corba.getObject('Logger', 'Logger')
            else:
                self.dao = dao
                
            if languages.has_key(lang.lower()) == False:
                raise ValueError("Invalid language provided to SessionLogger.")
            else:
                lang_code = languages[lang.lower()]
                self.session_id = self.dao.CreateSession(lang_code, name)

            if self.session_id == 0:
                raise LoggingException("Invalid arguments provided to CreateSession: %s, %s." % (lang_code, name))

            self.__load_action_codes()

            return True
        except Exception, e:
            if self.should_throw_exceptions:
                raise LoggingException(e)
            else:
                return False

    def create_request(self, source_ip, content, action_type, properties=[]):
        """
            Creates a request object on the server.
            Returns a new LogRequest object or None on error.
        """
        try:
            request_id = self.__server_create_request(source_ip, content, action_type, properties)
            log_request = LogRequest(self.dao, request_id)

            return log_request
        except Exception, e:
            if self.should_throw_exceptions:
                raise LoggingException(e)
            else:
                return None


    def create_request_login(self, source_ip, content, action_type, properties=[]):
        """
            Creates a login request object on the server.
            Returns a new LogRequestLogin or None on error.
        """
        try:
            request_id = self.__server_create_request(source_ip, content, action_type, properties)
            log_request = LogRequestLogin(self.dao, request_id, self.session_id)

            return log_request
        except Exception, e:
            if self.should_throw_exceptions:
                raise LoggingException(e)
            else:
                return None


    def close_session(self):
        """ 
            Tells the server to close this logging session.
            Returns True iff session closed successfully.
            """
        try:
            rc = self.dao.CloseSession(self.session_id)
            if rc == 0:
              raise LoggingException("CloseSession failed.")

            return True
        except Exception, e:
            if self.should_throw_exceptions:
                raise LoggingException(e)
            else:
                return False


    def __load_action_codes(self):
        """
            Request (action string code -> action int code) mapping from
            the server. 
            """
        #TODO: Fix this after server fix
        action_list = self.dao.GetServiceActions(self.service_type)
        self.actions = {"ClientLogin" : 100, "ClientLogout" : 101, "DomainFilter" : 1302, "FileFilter" : 1303, "DomainDetail" : 1304 }
        for (id, status) in action_list:
            self.actions[status] = id


    def __server_create_request(self, source_ip, content, action_type, properties):
        """
           Tell the server to create a new logging request.
           Returns request id iff request has been created successfully.
        """
        if not self.actions.has_key(action_type):
            raise ValueError("Invalid action type provided to CreateRequest: %s." % (action_type,))

        if content is None:
            content = ""

        try:
            request_id = self.dao.CreateRequest(source_ip, service_type_webadmin, content, properties, self.actions[action_type], self.session_id)
        except omniORB.CORBA.BAD_PARAM, e:
            raise LoggingException("CreateRequest failed with args: %s, %s, %s, %s, %s, %s. Original exception: %s" % \
                (source_ip, service_type_webadmin, content, properties, self.actions[action_type], self.session_id, str(e)))
        if request_id == 0:
            raise LoggingException("CreateRequest failed.")

        return request_id


class LogRequest(object):
    """ 
        A request for logging. Use one LogRequest object for one action to be logged and use 
        the update method to log the necessary information for this action.

        Should NOT be instantiated directly; use SessionLogger.create_request.

        Example usage: 
            req = session_logger.create_request(...)
            req.update("session_id", 132)
            ...
            req.commit("<foo/>")
    """

    def __init__(self, dao, request_id, throws_exceptions=False):
        self.dao = dao
        self.request_id = request_id
        self.should_throw_exceptions = throws_exceptions


    def update(self, name, value, output=False, child=False):
        """ Add a new row to the log request. """
        try:
            rc = self.dao.UpdateRequest(self.request_id, [ccReg.RequestProperty(name, value, output, child)])
            if not rc:
                raise LoggingException("UpdateSession failed.")
            return True
        except Exception, e:
            if self.should_throw_exceptions:
                raise LoggingException(e)
            else:
                return False


    def update_multiple(self, properties):
        """ Add multiple rows to the log request. """
        try:
            prop_list = properties if isinstance(properties, list) else [properties]
            props = [ccReg.RequestProperty(name, value, output, child) for (name, value, output, child) in prop_list]
            rc = self.dao.UpdateRequest(self.request_id, props)
            if not rc:
                raise LoggingException("UpdateSession failed.")
            return True
        except Exception, e:
            if self.should_throw_exceptions:
                raise LoggingException(e)
            else:
                return False


    def commit(self, content):
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
                return False


class LogRequestLogin(LogRequest):
    """ 
        A request for logging a login action.
        See LogRequest class for further information.
        Should NOT be instantiated directly; use SessionLogger.create_request_login.
    """
    def __init__(self, dao, request_id, session_id, throws_exceptions=False):
        LogRequest.__init__(self, dao, request_id, throws_exceptions)
        self.session_id = session_id

    def commit(self, content):
        try:

            rc = self.dao.CloseRequestLogin(self.request_id, content, [], self.session_id)
            if not rc:
                raise LoggingException("CloseRequest failed.")
            return True
        except Exception, e:
            if self.should_throw_exceptions:
                raise LoggingException(e)
            else:
                return False


class LoggingException(Exception):
    """ Generic exception thrown by this logging framework when something
        goes wrong. """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
