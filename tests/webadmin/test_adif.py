# -*- coding: utf-8 -*

import mox
from omniORB import CORBA
import cherrypy
import twill
import datetime
from logging import error
from achoo import calling
try:
    import ldap
except:
    error("Could not import ldap, some test will probably fail...")

from StringIO import StringIO
import twill.commands

try:
    from fred_webadmin.auth import ldap_auth, corba_auth
except:
    error("Could not import auth module, some test will probably fail...")

import tests.webadmin.base as base
import fred_webadmin.controller.adif

from fred_webadmin.corba import Registry, ccReg
import pylogger.dummylogger as logger
import fred_webadmin.user as user

class BaseADIFTestCase(base.DaphneTestCase):
    def setUp(self):
        base.DaphneTestCase.setUp(self)
        self.admin_mock = AdminMock()
        self.web_session_mock['Admin'] = self.admin_mock
        self.web_session_mock['user'] = user.User(UserMock())
        self.file_mgr_mock = FileManagerMock()
        self.web_session_mock['FileManager'] = self.file_mgr_mock
        self.corba_conn_mock = CorbaConnectionMock(admin=self.admin_mock)
        self.monkey_patch(
            fred_webadmin.controller.adif, 'corba_obj', self.corba_conn_mock)
        # Create the application, mount it and start the server.
        root = fred_webadmin.controller.adif.prepare_root()
        wsgiApp = cherrypy.tree.mount(root)
        cherrypy.server.start()
        # Redirect HTTP requests.
        twill.add_wsgi_intercept('localhost', 8080, lambda : wsgiApp)
        # Keep Twill quiet (suppress normal Twill output).
        self.outp = StringIO()
        twill.set_output(self.outp)

    def tearDown(self):
        base.DaphneTestCase.tearDown(self)
        # Remove the intercept.
        twill.remove_wsgi_intercept('localhost', 8080) 
        # Shut down Cherrypy server.
        cherrypy.server.stop()


class CertificationManagerMock(object):
    def __init__(self):
        super(CertificationManagerMock, self).__init__()

    def getCertificationsByRegistrar(self, reg_id):
        return []
        #[Registry.Registrar.Certification.CertificationData(
        #    1, ccReg.DateType(1, 1, 2008), ccReg.DateType(1, 1, 2010), 2, 17)]

    def createCertification(self, reg_id, from_date, to_date, score, file_id):
        return 17

    def updateCertification(self, crt_id, score, file_id):
        pass

    def shortenCertification(self, crt_id, to_date):
        raise NotImplementedError("This has to be stubbed out!")


class FileManagerMock(object):
    def info(self, file_id):
        raise NotImplementedError("This has to be stubbed out!")

    def save(self, name, mimetype, filetype):
        raise NotImplementedError("This has to be stubbed out!")


class AdminMock(object):
    def __init__(self):
        super(AdminMock, self).__init__()
        self.session = None
        
    def getCountryDescList(self):
        return [Registry.CountryDesc(1, 'cz')]

    def getDefaultCountry(self):
        return 1

    def getGroupManager(self):
        return GroupManagerMock()

    def getCertificationManager(self):
        return CertificationManagerMock()

    def authenticateUser(self):
        pass

    def createSession(self, username):
        self.session = SessionMock()
        return "testSessionString"

    def getSession(self, session_str):
        return self.session

    def authenticateUser(self, user, pwd):
        pass


class CorbaConnectionMock(object):
    def __init__(self, admin=AdminMock(), logger=logger.DummyLogger(), mailer=None, filemgr=None, messages=None):
        super(CorbaConnectionMock, self).__init__()
        self.obj = {
            "ccReg.Admin": admin,
            "ccReg.Logger": logger,
            "ccReg.Mailer": mailer,
            "ccReg.FileManager": filemgr,
            "Registry.Messages": messages,
        }

    def getObject(self, obj1, obj2):
        return self.obj[obj2] 

    def connect(self, user, pwd):
        pass

class SessionMock(object):
    def __init__(self):
        super(SessionMock, self).__init__()

    def getUser(self):
        return UserMock()

    def setHistory(self, val):
        pass

    def getDetail(self, obj, id):
        pass

    def updateRegistrar(self, reg):
        raise NotImplementedError("This has to be stubbed out!")

    def getBankingInvoicing(self):
        raise NotImplementedError("This has to be stubbed out!")
        
        
class UserMock(object):
    def __init__(self):
        super(UserMock, self).__init__()

    def _get_id(self):
        return "test_user_id"

    def _get_username(self):
        return "test_username"

    def _get_firstname(self):
        return "test_firstname"

    def _get_surname(self):
        return "test_surname"

class GroupManagerMock(object):
    def __init__(self):
        self.groups = [
            Registry.Registrar.Group.GroupData(
                1, "test_group_1", ccReg.DateType(0, 0, 0)),
            Registry.Registrar.Group.GroupData(
                10, "test_group_2", ccReg.DateType(20, 10, 2009)),
            Registry.Registrar.Group.GroupData(
                7, "test_group_3", ccReg.DateType(0, 0, 0))]

    def getGroups(self):
        return self.groups

    def getMembershipsByRegistar(self, reg_id):
        return []
#        return [Registry.Registrar.Group.MembershipByRegistrar(1, 7,
#            ccReg.DateType(1, 1, 2008), ccReg.DateType(20, 10, 2010))]

    def deleteGroup(self, group_id):
        raise NotImplementedError("This has to be stubbed out!")

    def addRegistrarToGroup(self, reg_id, group_id):
        raise NotImplementedError("This has to be stubbed out!")
        
    def removeRegistrarFromGroup(self, reg_id, group_id):
        raise NotImplementedError("This has to be stubbed out!")


class TestADIF(BaseADIFTestCase):
    def setUp(self):
        BaseADIFTestCase.setUp(self)
   
    def test_login_valid_corba_auth(self):
        """ Login passes when using valid corba authentication.
        """
        fred_webadmin.config.auth_method = 'CORBA'
        # Replace fred_webadmin.controller.adif.auth module with CORBA
        # module.
        self.monkey_patch(
            fred_webadmin.controller.adif, 'auth', corba_auth)
        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/login")
        twill.commands.showforms()
        twill.commands.fv(1, "login", "test")
        twill.commands.fv(1, "password", "test pwd")
        twill.commands.fv(1, "corba_server", "0")
        twill.commands.submit()
        twill.commands.url("http://localhost:8080/summary/")
        twill.commands.code(200)

    '''def ignoretest_login_unicode_username(self):
        """ Login passes when using valid corba authentication.
            THIS IS BROKEN, probably because of strange way 
            mechanize (and twill that uses it) handles unicode strings.
        """
        fred_webadmin.config.auth_method = 'CORBA'
        # Replace fred_webadmin.controller.adif.auth module with CORBA
        # module.
        self.monkey_patch(
            fred_webadmin.controller.adif, 'auth', corba_auth)
        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/login")
        twill.commands.showforms()
        twill.commands.fv(1, "login", u"ěščěšřéýí汉语unicode")
        twill.commands.fv(1, "password", "test pwd")
        twill.commands.fv(1, "corba_server", "0")
        twill.commands.submit()
        twill.commands.url("http://localhost:8080/summary/")
        twill.commands.code(200)'''


    def test_login_invalid_corba_auth(self):
        """ Login fails when using invalid corba authentication.
        """
        fred_webadmin.config.auth_method = 'CORBA'
        self.monkey_patch(
            fred_webadmin.controller.adif, 'auth', corba_auth)
        self.corba_mock.StubOutWithMock(self.admin_mock, "authenticateUser")
        self.admin_mock.authenticateUser(
            "test", "test pwd").AndRaise(ccReg.Admin.AuthFailed)
        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/login")
        twill.commands.showforms()
        twill.commands.fv(1, "login", "test")
        twill.commands.fv(1, "password", "test pwd")
        twill.commands.fv(1, "corba_server", "0")
        twill.commands.submit()
        twill.commands.url("http://localhost:8080/login/")
        twill.commands.code(403)


    def test_login_ldap_valid_credentials(self):
        """ Login passes when valid credentials are supplied when using LDAP.
        """
        fred_webadmin.config.auth_method = 'LDAP'
        fred_webadmin.config.LDAP_scope = "test ldap scope %s"
        fred_webadmin.config.LDAP_server = "test ldap server"
        # Replace fred_webadmin.controller.adif.auth module with ldap
        # module.
        self.monkey_patch(
            fred_webadmin.controller.adif, 'auth', ldap_auth)
        # Mock out ldap.open method. We must not mock the whole ldap package,
        # because ldap_auth uses ldap exceptions.
        self.monkey_patch(
            fred_webadmin.auth.ldap_auth.ldap, 'open', self.ldap_mock)
        fred_webadmin.auth.ldap_auth.ldap.open.__call__(
            "test ldap server").AndReturn(self.ldap_mock)
        self.ldap_mock.simple_bind_s("test ldap scope test", "test pwd")
        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/login")
        twill.commands.showforms()
        twill.commands.fv(1, "login", "test")
        twill.commands.fv(1, "password", "test pwd")
        twill.commands.fv(1, "corba_server", "0")
        twill.commands.submit()
        # Invalid credentials => stay at login page.
        twill.commands.url("http://localhost:8080/summary/")
        twill.commands.code(200)

    def test_login_ldap_invalid_credentials(self):
        """ Login fails when invalid credentials are supplied when using LDAP.
        """
        # Use LDAP for authenication.
        fred_webadmin.config.auth_method = 'LDAP'
        fred_webadmin.config.LDAP_scope = "test ldap scope %s"
        fred_webadmin.config.LDAP_server = "test ldap server"
        # Replace fred_webadmin.controller.adif.auth module with ldap
        # module.
        self.monkey_patch(
            fred_webadmin.controller.adif, 'auth', ldap_auth)
        # Mock out ldap.open method.
        self.monkey_patch(
            fred_webadmin.auth.ldap_auth.ldap, 'open', self.ldap_mock)
        fred_webadmin.auth.ldap_auth.ldap.open.__call__(
            "test ldap server").AndReturn(self.ldap_mock)
        self.ldap_mock.simple_bind_s(
            "test ldap scope test", "test pwd").AndRaise(
                ldap.INVALID_CREDENTIALS)
        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/login")
        twill.commands.showforms()
        twill.commands.fv(1, "login", "test")
        twill.commands.fv(1, "password", "test pwd")
        twill.commands.fv(1, "corba_server", "0")
        twill.commands.submit()
        # Invalid credentials => stay at login page.
        twill.commands.url("http://localhost:8080/login/")
        twill.commands.code(403)

    def test_login_ldap_server_down(self):
        """ Login fails when using LDAP and LDAP server is down.
        """
        # Use LDAP for authenication.
        fred_webadmin.config.auth_method = 'LDAP'
        fred_webadmin.config.LDAP_scope = "test ldap scope %s"
        fred_webadmin.config.LDAP_server = "test ldap server"
        # Replace fred_webadmin.controller.adif.auth module with ldap
        # module.
        self.monkey_patch(
            fred_webadmin.controller.adif, 'auth', ldap_auth)
        # Mock out ldap.open method.
        self.monkey_patch(
            fred_webadmin.auth.ldap_auth.ldap, 'open', self.ldap_mock)
        fred_webadmin.auth.ldap_auth.ldap.open.__call__(
            "test ldap server").AndRaise(ldap.SERVER_DOWN)
        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/login")
        twill.commands.showforms()
        twill.commands.fv(1, "login", "test")
        twill.commands.fv(1, "password", "test pwd")
        twill.commands.fv(1, "corba_server", "0")
        twill.commands.submit()
        # Invalid credentials => stay at login page.
        twill.commands.url("http://localhost:8080/login/")

    def test_double_login(self):
        """ Loging in when already loged in redirects to /summary. 
        """
        self.web_session_mock['corbaSessionString'] = "test session string"
        self.corba_mock.ReplayAll()
        twill.commands.go("http://localhost:8080/login/")
        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/summary/")

    def test_login_invalid_form(self):
        """ Login fails when submitting invalid form.
        """
        self.corba_mock.ReplayAll()
        twill.commands.go("http://localhost:8080/login/")
        twill.commands.showforms()
        twill.commands.fv(1, "login", "")
        twill.commands.fv(1, "password", "")
        twill.commands.code(200)
        # Check that we did not leave the login page.
        twill.commands.url("http://localhost:8080/login/")


class RegistrarUtils(object):
    def _fabricate_registrar(self):
        """ Returns a fake Registrar object. """ 
        return (
            CORBA.Any(
                CORBA.TypeCode("IDL:Registry/Registrar/Detail:1.0"),
                Registry.Registrar.Detail(
                    id=42L, ico='', dic='', varSymb='', vat=True, 
                    handle='test handle', name='Company l.t.d.', 
                    organization='test org 1', street1='', 
                    street2='', street3='', city='', stateorprovince='', 
                    postalcode='', country='CZ', telephone='', fax='', 
                    email='', url='www.nic.cz', credit='0.00', 
                    unspec_credit=u'120.00',
                    access=[Registry.Registrar.EPPAccess(
                        password='123456789', 
                        md5Cert='60:7E:DF:39:62:C3:9D:3C:EB:5A:87:80:C1:73:4F:99'), 
                    Registry.Registrar.EPPAccess(
                        password='passwd', 
                        md5Cert='39:D1:0C:CA:05:3A:CC:C0:0B:EC:6F:3F:81:0D:C7:9E')], 
                    zones=[
                        Registry.Registrar.ZoneAccess(
                            id=1L, name='0.2.4.e164.arpa', credit='0', 
                            fromDate=ccReg.DateType(1, 1, 2007),
                            toDate=ccReg.DateType(0, 0, 0)), 
                        Registry.Registrar.ZoneAccess(
                            id=2L, name='cz', credit='0',
                            fromDate=ccReg.DateType(1, 1, 2007),
                            toDate=ccReg.DateType(0, 0, 0))], hidden=False)))


class TestRegistrar(BaseADIFTestCase, RegistrarUtils):
    def __init__(self):
        super(TestRegistrar, self).__init__()

    def setUp(self):
        super(TestRegistrar, self).setUp()
        # We have to return our special session (createSession would
        # instantiate a new one).
        self.admin_mock.createSession("testuser")
        self.session_mock = self.admin_mock.getSession("testSessionString")
        self.corba_mock.StubOutWithMock(self.session_mock, "getDetail")
        self.corba_mock.StubOutWithMock(self.session_mock, "updateRegistrar")

    def test_edit_correct_args(self):
        """ Registrar editation passes. """
        self.corba_mock.StubOutWithMock(self.file_mgr_mock, "info")
        self.file_mgr_mock.info(17).AndReturn(ccReg.FileInfo(1, "testfile",
            "testpath", "testmime", 0, ccReg.DateType(10, 10, 2010), 100))
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.file_mgr_mock.info(17).AndReturn(ccReg.FileInfo(1, "testfile",
            "testpath", "testmime", 0, ccReg.DateType(10, 10, 2010), 100))
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.file_mgr_mock.info(17).AndReturn(ccReg.FileInfo(1, "testfile",
            "testpath", "testmime", 0, ccReg.DateType(10, 10, 2010), 100))
        self.session_mock.updateRegistrar(
            mox.IsA(Registry.Registrar.Detail)).AndReturn(42)
        # Jumps to detail after updating.
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.file_mgr_mock.info(17).AndReturn(ccReg.FileInfo(1, "testfile",
            "testpath", "testmime", 0, ccReg.DateType(10, 10, 2010), 100))

        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/registrar/edit/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/registrar/detail/\?id=42")
        twill.commands.find("test handle")

    def test_edit_incorrect_zone_date_arg(self):
        """ Registrar editation does not pass when invalid zone date 
            provided. """
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.session_mock.updateRegistrar(
            mox.IsA(Registry.Registrar.Detail)).AndReturn(42)
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())

        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/registrar/edit/?id=42")
        twill.commands.showforms()

        twill.commands.fv(2, "handle", "test handle")
        twill.commands.fv(2, "zones-0-toDate", "test invalid date")
        twill.commands.submit()

        # Test that we stay in edit, because the form is not valid.
        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/registrar/edit/\?id=42")

    def test_create(self):
        """ Registrar creation passes.
        """
        # Submit the form.
        self.session_mock.updateRegistrar(
            mox.IsA(ccReg.AdminRegistrar)).AndReturn(42)

        # Display the registar detail (we're redirected after a successful
        # submit).
        self.session_mock.getDetail(ccReg.FT_REGISTRAR, 42).AndReturn(
            CORBA.Any(
                CORBA.TypeCode("IDL:Registry/Registrar/Detail:1.0"), 
                Registry.Registrar.Detail(
                    id=u'0', ico='', dic='', varSymb='', vat=True, 
                    handle='test handle', name='', 
                    organization='', street1='', 
                    street2='', street3='', city='', stateorprovince='', 
                    postalcode='', country='', telephone='', fax='', 
                    email='', url='', credit='', 
                    unspec_credit=u'', access=[], zones=[], hidden=False)))

        self.corba_mock.ReplayAll()

        # Create the registrar.
        twill.commands.go("http://localhost:8080/registrar/create")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.submit()

        # Test that we've jumped to the detail page (i.e., creation has
        # completed successfully).
        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/registrar/detail/\?id=42")
        twill.commands.find("test handle")

    def test_create_registrar_zone_to_date_smaller_than_zone_from_date(self):
        """ Registrar creation fails when zone 'To' date is smaller than zone
            'From' date (ticket #3530)."""
        self.session_mock.updateRegistrar(
            mox.IsA(ccReg.AdminRegistrar)).AndReturn(42)
        self.session_mock.getDetail(ccReg.FT_REGISTRAR, 42).AndReturn(
            CORBA.Any(
                CORBA.TypeCode("IDL:Registry/Registrar/Detail:1.0"), 
                Registry.Registrar.Detail(
                    id=3L, ico='', dic='', varSymb='', vat=True, 
                    handle='test handle', name='', 
                    organization='', street1='', 
                    street2='', street3='', city='', stateorprovince='', 
                    postalcode='', country='', telephone='', fax='', 
                    email='', url='', credit='', 
                    unspec_credit=u'', access=[], zones=[], hidden=False)))

        self.corba_mock.ReplayAll()

        # Create the registrar.
        twill.commands.go("http://localhost:8080/registrar/create")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        # Fill in the zone name (mandatory field).
        twill.commands.fv(2, "zones-0-name", "test zone")
        # 'To' date is smaller than 'From' date.
        twill.commands.fv(2, "zones-0-fromDate", "2010-02-01")
        twill.commands.fv(2, "zones-0-toDate", "2010-01-01")
        twill.commands.submit()

        # Check that we're still at the 'create' page (i.e., the registrar has
        # not been created.
        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/registrar/create")

    def test_create_registrar_zone_to_date_bigger_than_zone_from_date(self):
        """ Registrar creation passes when zone 'To' date is bigger than zone
            'From' date."""
        self.session_mock.updateRegistrar(
            mox.IsA(ccReg.AdminRegistrar)).AndReturn(42)
        self.session_mock.getDetail(ccReg.FT_REGISTRAR, 42).AndReturn(
            CORBA.Any(
                CORBA.TypeCode("IDL:Registry/Registrar/Detail:1.0"), 
                Registry.Registrar.Detail(
                    id=3L, ico='', dic='', varSymb='', vat=True, 
                    handle='test handle', name='', 
                    organization='', street1='', 
                    street2='', street3='', city='', stateorprovince='', 
                    postalcode='', country='', telephone='', fax='', 
                    email='', url='', credit='', 
                    unspec_credit=u'', access=[], 
                    zones=[Registry.Registrar.ZoneAccess(
                        id=5L, name='cz', credit='9453375', 
                        fromDate=ccReg.DateType(day=1, month=2, year=2010), 
                        toDate=ccReg.DateType(day=10, month=2, year=2010))], 
                    hidden=False)))

        self.corba_mock.ReplayAll()

        # Create the registrar.
        twill.commands.go("http://localhost:8080/registrar/create")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        # Fill in the zone name (mandatory field).
        twill.commands.fv(2, "zones-0-name", "test zone")
        # 'To' date is bigger than 'From' date.
        twill.commands.fv(2, "zones-0-fromDate", datetime.date.today().isoformat())
        twill.commands.fv(2, "zones-0-toDate", (datetime.date.today() + datetime.timedelta(7)).isoformat())
        twill.commands.submit()

        # Test that we've jumped to the detail page (i.e., creation has
        # completed successfully).
        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/registrar/detail/\?id=42")
        twill.commands.find("test handle")


    def test_create_two_registrars_with_same_name(self):
        """ Creating second registrar with the same name fails.
            Ticket #3079. """
        self.session_mock.updateRegistrar(
            mox.IsA(ccReg.AdminRegistrar)).AndReturn(42)
        self.session_mock.getDetail(ccReg.FT_REGISTRAR, 42).AndReturn(
            CORBA.Any(
                CORBA.TypeCode("IDL:Registry/Registrar/Detail:1.0"), 
                Registry.Registrar.Detail(
                    id=3L, ico='', dic='', varSymb='', vat=True, 
                    handle='test handle', name='', 
                    organization='', street1='', 
                    street2='', street3='', city='', stateorprovince='', 
                    postalcode='', country='', telephone='', fax='', 
                    email='', url='', credit='', 
                    unspec_credit=u'', access=[], zones=[], hidden=False)))

        self.corba_mock.ReplayAll()

        # Create the first registrar.
        twill.commands.go("http://localhost:8080/registrar/create")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/registrar/detail/\?id=42")
        twill.commands.find("test handle")

        self.corba_mock.ResetAll()

        # Now create the second one with the same name.
        self.session_mock.updateRegistrar(
            mox.IsA(ccReg.AdminRegistrar)).AndRaise(ccReg.Admin.UpdateFailed)

        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/registrar/create")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.submit()

        # Test that we've stayed at the 'create' page (i.e., creation has
        # failed).
        twill.commands.url("http://localhost:8080/registrar/create")
        twill.commands.code(200)


class TestRegistrarGroups(BaseADIFTestCase, RegistrarUtils):
    def setUp(self):
        BaseADIFTestCase.setUp(self)
        self.admin_mock.createSession("testuser")
        self.session_mock = self.admin_mock.getSession("testSessionString")
        self.corba_mock.StubOutWithMock(self.session_mock, "getDetail")
        self.corba_mock.StubOutWithMock(self.session_mock, "updateRegistrar")
        self.group_mgr_mock = GroupManagerMock()
        self.admin_mock.getGroupManager = lambda : self.group_mgr_mock


    def test_add_registrar_to_group(self):
        self.corba_mock.StubOutWithMock(
            self.group_mgr_mock, "getMembershipsByRegistar")
        self.corba_mock.StubOutWithMock(
            self.group_mgr_mock, "addRegistrarToGroup")

        # Prepare the groups.
        self.group_mgr_mock.getGroups = lambda : (
            [Registry.Registrar.Group.GroupData(
                1, "test_group_1", ccReg.DateType(0, 0, 0)),
            Registry.Registrar.Group.GroupData(
                3, "test_group_3", ccReg.DateType(20, 10, 2009)),
            Registry.Registrar.Group.GroupData(
                2, "test_group_2", ccReg.DateType(0, 0, 0))])

        # Show the edit form.
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.group_mgr_mock.getMembershipsByRegistar(42).AndReturn([])

        # Process form after submitting.
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.group_mgr_mock.getMembershipsByRegistar(42).AndReturn([])
        self.session_mock.updateRegistrar(
            mox.IsA(Registry.Registrar.Detail)).AndReturn(42)
        self.group_mgr_mock.getMembershipsByRegistar(42).AndReturn([])
        self.group_mgr_mock.addRegistrarToGroup(42, 1)

        # Jump to detail after updating.
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.group_mgr_mock.getMembershipsByRegistar(42).AndReturn(
            [Registry.Registrar.Group.MembershipByRegistrar(1, 1,
            ccReg.DateType(1, 1, 2008), ccReg.DateType(0, 0, 0))])

        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/registrar/edit/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "groups-0-id", "1")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.find("test_group_1")

        self.corba_mock.VerifyAll()

    def test_remove_registrar_from_group(self):
        self.corba_mock.StubOutWithMock(
            self.group_mgr_mock, "getMembershipsByRegistar")
        self.corba_mock.StubOutWithMock(
            self.group_mgr_mock, "removeRegistrarFromGroup")

        # Prepare the groups.
        self.group_mgr_mock.getGroups = lambda : (
            [Registry.Registrar.Group.GroupData(
                1, "test_group_1", ccReg.DateType(0, 0, 0)),
            Registry.Registrar.Group.GroupData(
                3, "test_group_3", ccReg.DateType(20, 10, 2009)),
            Registry.Registrar.Group.GroupData(
                2, "test_group_2", ccReg.DateType(0, 0, 0))])

        # Show the edit form.
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.group_mgr_mock.getMembershipsByRegistar(42).AndReturn(
            [Registry.Registrar.Group.MembershipByRegistrar(
                1, 1, ccReg.DateType(1, 1, 2008), ccReg.DateType(0, 0, 0))])

        # Process form after submitting.
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.group_mgr_mock.getMembershipsByRegistar(42).AndReturn(
            [Registry.Registrar.Group.MembershipByRegistrar(
                1, 1, ccReg.DateType(1, 1, 2008), ccReg.DateType(0, 0, 0))])
        self.session_mock.updateRegistrar(
            mox.IsA(Registry.Registrar.Detail)).AndReturn(42)
        self.group_mgr_mock.removeRegistrarFromGroup(42, 1)

        # Jump to detail after updating.
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.group_mgr_mock.getMembershipsByRegistar(42).AndReturn([])

        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/registrar/edit/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "groups-0-DELETE", "1")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.notfind("test_group_1")

        self.corba_mock.VerifyAll()


class TestRegistrarCertifications(BaseADIFTestCase, RegistrarUtils):
    def setUp(self):
        BaseADIFTestCase.setUp(self)
        self.admin_mock.createSession("testuser")
        self.session_mock = self.admin_mock.getSession("testSessionString")
        self.corba_mock.StubOutWithMock(self.session_mock, "getDetail")
        self.corba_mock.StubOutWithMock(self.session_mock, "updateRegistrar")

        self.cert_mgr_mock = CertificationManagerMock()
        self.admin_mock.getCertificationManager = lambda : self.cert_mgr_mock
        self.corba_mock.StubOutWithMock(
            self.cert_mgr_mock, "getCertificationsByRegistrar")
        self.corba_mock.StubOutWithMock(
            self.cert_mgr_mock, "createCertification")

        self.file_mgr_mock = FileManagerMock()
        self.web_session_mock['FileManager'] = self.file_mgr_mock
        self.corba_mock.StubOutWithMock(
            self.file_mgr_mock, "save")

    def test_add_certification(self):
        """ Correctly configured certification is added.
        """
        # Show the edit form.
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.cert_mgr_mock.getCertificationsByRegistrar(42).AndReturn([])

        # Process form after submitting.
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.cert_mgr_mock.getCertificationsByRegistrar(42).AndReturn([])
        self.session_mock.updateRegistrar(
            mox.IsA(Registry.Registrar.Detail)).AndReturn(42)
        file_upload_mock = self.corba_mock.CreateMockAnything()
        self.file_mgr_mock.save(
            "./tests/webadmin/foofile.bar", "application/octet-stream",
            6).AndReturn(file_upload_mock)
        file_upload_mock.finalize_upload().AndReturn(17)
        self.cert_mgr_mock.createCertification(
            42, mox.IsA(ccReg.DateType), mox.IsA(ccReg.DateType), 2, 17)

        # Jump to detail after updating.
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.cert_mgr_mock.getCertificationsByRegistrar(42).AndReturn(
            [Registry.Registrar.Certification.CertificationData(
                1, ccReg.DateType(1, 1, 2008), 
                ccReg.DateType(1, 1, 2010), 2, 17)])

        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/registrar/edit/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "certifications-0-fromDate", "2010-06-01")
        twill.commands.fv(2, "certifications-0-toDate", "2011-06-01")
        twill.commands.fv(2, "certifications-0-score", "2")
        twill.commands.formfile(2, "certifications-0-evaluation_file", "./tests/webadmin/foofile.bar")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/registrar/detail/\?id=42")
        twill.commands.showforms()
        twill.commands.find(
            '''<a href="/file/detail/\?id=17"''')

        self.corba_mock.VerifyAll()

    def test_add_certification_no_file(self):
        """ Certification is not added when no file has been uploaded.
        """
        # Show the edit form.
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.cert_mgr_mock.getCertificationsByRegistrar(42).AndReturn([])

        # Process form after submitting.
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.cert_mgr_mock.getCertificationsByRegistrar(42).AndReturn([])
        self.session_mock.updateRegistrar(
            mox.IsA(Registry.Registrar.Detail)).AndReturn(42)

        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/registrar/edit/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "certifications-0-fromDate", "2010-06-01")
        twill.commands.fv(2, "certifications-0-toDate", "2011-06-01")
        twill.commands.fv(2, "certifications-0-score", "2")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/registrar/edit/\?id=42")

        self.corba_mock.VerifyAll()

    class DateMock(object):
            """ Mock class to replace datetime.date.today()
                (we do not want it to return the real current date).
            """
            @classmethod
            def today(cls):
                return datetime.date(2008, 1, 1)

    def test_shorten_certification(self):
        """ It is possible to shorten the certification.
        """
        self.corba_mock.StubOutWithMock(
            self.cert_mgr_mock, "shortenCertification")
        self.corba_mock.StubOutWithMock(
            self.file_mgr_mock, "info")

        date_mock = TestRegistrarCertifications.DateMock
        self.monkey_patch(
            fred_webadmin.webwidgets.forms.editforms, 
            'date', date_mock)

        # Show the edit form.
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.cert_mgr_mock.getCertificationsByRegistrar(42).AndReturn(
            [Registry.Registrar.Certification.CertificationData(
                1, ccReg.DateType(1, 1, 2008), 
                ccReg.DateType(1, 1, 2010), 2, 17)])

        # Process form after submitting.
        self.file_mgr_mock.info(17).AndReturn(ccReg.FileInfo(1, "testfile",
            "testpath", "testmime", 0, ccReg.DateType(10, 10, 2010), 100))
        self.file_mgr_mock.info(17).AndReturn(ccReg.FileInfo(1, "testfile",
            "testpath", "testmime", 0, ccReg.DateType(10, 10, 2010), 100))
        self.session_mock.getDetail(
           ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.cert_mgr_mock.getCertificationsByRegistrar(42).AndReturn(
            [Registry.Registrar.Certification.CertificationData(
                1, ccReg.DateType(1, 1, 2008), 
                ccReg.DateType(1, 1, 2010), 2, 17)])
        self.file_mgr_mock.info(17).AndReturn(ccReg.FileInfo(1, "testfile",
            "testpath", "testmime", 0, ccReg.DateType(10, 10, 2010), 100))
    
        self.session_mock.updateRegistrar(
            mox.IsA(Registry.Registrar.Detail)).AndReturn(42)
        self.cert_mgr_mock.shortenCertification(1, mox.IsA(ccReg.DateType))

        # Jump to detail after updating (show shortened toDate).
        self.session_mock.getDetail(
            ccReg.FT_REGISTRAR, 42).AndReturn(self._fabricate_registrar())
        self.cert_mgr_mock.getCertificationsByRegistrar(42).AndReturn(
            [Registry.Registrar.Certification.CertificationData(
                1, ccReg.DateType(1, 1, 2008), 
                ccReg.DateType(12, 12, 2009), 2, 17)])
        self.file_mgr_mock.info(17).AndReturn(ccReg.FileInfo(1, "testfile",
            "testpath", "testmime", 0, ccReg.DateType(10, 10, 2010), 100))

        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/registrar/edit/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "certifications-0-toDate", "2009-12-12")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/registrar/detail/\?id=42")
        twill.commands.showforms()
        twill.commands.find(
            '''<a href="/file/detail/\?id=17"''')
        twill.commands.find("2009-12-12")

        self.corba_mock.VerifyAll()


class TestBankStatement(BaseADIFTestCase):
    def setUp(self):
        super(TestBankStatement, self).setUp()
        self.admin_mock.createSession("testuser")
        self.session_mock = self.admin_mock.getSession("testSessionString")
        self.corba_mock.StubOutWithMock(self.session_mock, "getDetail")
        self.corba_mock.StubOutWithMock(
            self.session_mock, "getBankingInvoicing")

    def _fabricate_bank_statement_detail(self):
        """ Create a fake Registry.Banking.BankItem.Detail object for testing
            purposes. """
        return CORBA.Any(
                CORBA.TypeCode("IDL:Registry/Banking/BankItem/Detail:1.0"),
                Registry.Banking.BankItem.Detail(
                    id=16319L, statementId=5106L, accountNumber='756', 
                    bankCodeId='2400', code=2, type=1, konstSym='598', 
                    varSymb='', specSymb='', price='1.62', 
                    accountEvid='07-14-2-756/2400', accountDate='31.07.2007',
                    accountMemo='Urok 07/2007', invoiceId=0L, 
                    accountName='CZ.NIC, z.s.p.o.', 
                    crTime='31.07.2007 02:00:00'))

    def test_successfull_statementitem_payment_pairing(self):
        """ Payment pairing works OK when correct registrar handle 
            is specified. """
        statement = self._fabricate_bank_statement_detail()
        self.session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement)
        invoicing_mock = self.corba_mock.CreateMockAnything()
        self.session_mock.getBankingInvoicing().AndReturn(invoicing_mock)
        invoicing_mock.pairPaymentRegistrarHandle(
            42, "test handle").AndReturn(True)
        invoicing_mock.setPaymentType(42, 2).AndReturn(True)
        # Create a new bank statement detail with a non-zero invoiceId value 
        # to simulate successfull payment pairing.
        statement_after_pairing = self._fabricate_bank_statement_detail()
        statement_after_pairing.value().invoiceId = 11L
        statement_after_pairing.value().type = 2
        self.session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement_after_pairing)

        self.corba_mock.ReplayAll()

        # Go to the pairing form 
        twill.commands.go("http://localhost:8080/bankstatement/detail/?id=42")
        fs = twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.fv(2, "type", "2")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/bankstatement/detail/\?id=42")
        # Check that we display a link to the invoice after a successfull
        # payment.
        twill.commands.code(200)
        twill.commands.find("""<a href="/invoice/detail/\?id=11">.*</a>""")

    def test_successfull_statementitem_payment_pairing_no_reg_handle(self):
        """ Payment pairing works OK when correct registrar handle 
            is not specified, but type != "from/to registrar". """
        statement = self._fabricate_bank_statement_detail()
        self.session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement)
        invoicing_mock = self.corba_mock.CreateMockAnything()
        self.session_mock.getBankingInvoicing().AndReturn(invoicing_mock)
        invoicing_mock.setPaymentType(42, 3).AndReturn(True)
        # Create a new bank statement detail with a non-zero invoiceId value 
        # to simulate successfull payment pairing.
        statement_after_pairing = self._fabricate_bank_statement_detail()
        statement_after_pairing.value().invoiceId = 11L
        statement_after_pairing.value().type = 3
        self.session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement_after_pairing)

        self.corba_mock.ReplayAll()

        # Go to the pairing form 
        twill.commands.go("http://localhost:8080/bankstatement/detail/?id=42")
        fs = twill.commands.showforms()
        twill.commands.fv(2, "type", "3")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/bankstatement/detail/\?id=42")
        # Check that we do not display a link to the invoice after a successfull
        # payment (because it's not paired with a registrar).
        twill.commands.code(200)
        twill.commands.notfind("""<a href="/invoice/detail/\?id=11">.*</a>""")

    def test_successfull_statementitem_payment_pairing_incorrect_reg_handle(self):
        """ Payment pairing works OK when an invalid registrar handle 
            is specified, but type != "from/to registrar". """
        statement = self._fabricate_bank_statement_detail()
        self.session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement)
        invoicing_mock = self.corba_mock.CreateMockAnything()
        self.session_mock.getBankingInvoicing().AndReturn(invoicing_mock)
        invoicing_mock.setPaymentType(42, 3).AndReturn(True)
        # Create a new bank statement detail with a non-zero invoiceId value 
        # to simulate successfull payment pairing.
        statement_after_pairing = self._fabricate_bank_statement_detail()
        statement_after_pairing.value().invoiceId = 11L
        statement_after_pairing.value().type = 3
        self.session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement_after_pairing)

        self.corba_mock.ReplayAll()

        # Go to the pairing form 
        twill.commands.go("http://localhost:8080/bankstatement/detail/?id=42")
        fs = twill.commands.showforms()
        twill.commands.fv(2, "handle", "invalid handle")
        twill.commands.fv(2, "type", "3")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/bankstatement/detail/\?id=42")
        # Check that we do not display a link to the invoice after a successfull
        # payment (because it's not paired with a registrar).
        twill.commands.code(200)
        twill.commands.notfind("""<a href="/invoice/detail/\?id=11">.*</a>""")


    def test_statementitem_detail_unknown_unempty_handle(self):
        """ Pairing with unknown registrar handle fails.
        """
        statement = self._fabricate_bank_statement_detail()
        self.session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement)
        invoicing_mock = self.corba_mock.CreateMockAnything()
        self.session_mock.getBankingInvoicing().AndReturn(invoicing_mock)
        invoicing_mock.pairPaymentRegistrarHandle(
            42, "test handle").AndReturn(False)
        self.session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement)

        self.corba_mock.ReplayAll()

        # Go to the pairing form 
        twill.commands.go("http://localhost:8080/bankstatement/detail/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.fv(2, "type", "2")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/bankstatement/detail/\?id=42")
        # Check that we do not display a link to the invoice after an 
        # unsuccessful payment attempt.
        twill.commands.notfind("""<a href="/invoice/detail/\?id=11">.*</a>""")

    def test_statementitem_detail_empty_handle(self):
        """ Pairing payment with empty registrar handle fails.
        """
        statement = self._fabricate_bank_statement_detail()
        self.session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement)
        invoicing_mock = self.corba_mock.CreateMockAnything()
        self.session_mock.getBankingInvoicing().AndReturn(invoicing_mock)
        invoicing_mock.pairPaymentRegistrarHandle(
            42, "test handle").AndReturn(False)
        self.session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement)

        self.corba_mock.ReplayAll()

        # Go to the pairing form 
        twill.commands.go("http://localhost:8080/bankstatement/detail/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.fv(2, "type", "2")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/bankstatement/detail/\?id=42")
        # Check that we do not display a link to the invoice after
        #an unsuccessful payment attempt.
        twill.commands.notfind("""<a href="/invoice/detail/\?id=11">.*</a>""")

    def test_statementitem_detail_no_perms_to_change_type(self):
        """ Pairing payment with empty registrar handle fails.
        """
        cherrypy.session['user']._authorizer = self.authorizer_mock
        statement = self._fabricate_bank_statement_detail()
        self.session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement)
        invoicing_mock = self.corba_mock.CreateMockAnything()
        self.session_mock.getBankingInvoicing().AndReturn(invoicing_mock)
        invoicing_mock.pairPaymentRegistrarHandle(
            42, "test handle").AndReturn(False)
        self.session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement)
        self.authorizer_mock.has_permission(
            'bankstatement', 'read').AndReturn(True)
        self.authorizer_mock.has_permission(
            'bankstatement', 'change').AndReturn(False)
        # Other permissions get checked here (possibly will change when
        # permission caching is implemented).
        for i in range(0, 50):
            self.authorizer_mock.has_permission(
                mox.IgnoreArg(), mox.IgnoreArg()).AndReturn(False)

        self.corba_mock.ReplayAll()

        # Go to the pairing form 
        twill.commands.go("http://localhost:8080/bankstatement/detail/?id=42")
        twill.commands.showforms()
        twill.commands.notfind("""<input type="text" name="handle" value=\"\"""")


class TestLoggerNoLogView(BaseADIFTestCase):
    def setUpConfig(self):
        fred_webadmin.config.debug = False
        fred_webadmin.config.auth_method = 'CORBA'
        fred_webadmin.config.audit_log['viewing_actions_enabled'] = False
        fred_webadmin.config.audit_log['logging_actions_enabled'] = False
        fred_webadmin.config.audit_log['force_critical_logging'] = False

    def setUp(self):
        self.setUpConfig()
        BaseADIFTestCase.setUp(self)

    def test_logger_hidden_when_log_view_is_disabled_in_config(self):
        # Replace fred_webadmin.controller.adif.auth module with CORBA
        # module.
        print
        self.monkey_patch(
            fred_webadmin.controller.adif, 'auth', corba_auth)

        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/login")
        twill.commands.showforms()
        twill.commands.fv(1, "login", "test")
        twill.commands.fv(1, "password", "test pwd")
        twill.commands.fv(1, "corba_server", "0")
        twill.commands.submit()

        twill.commands.go("http://localhost:8080/logger")
        twill.commands.url("http://localhost:8080/logger")
        # Test that the page has not been found.
        twill.commands.code(404)


class TestLoggerLogView(BaseADIFTestCase):
    def setUpConfig(self):
        fred_webadmin.config.auth_method = 'CORBA'
        fred_webadmin.config.audit_log['viewing_actions_enabled'] = True


class TestRegistrarGroupEditor(BaseADIFTestCase):
    def setUp(self):
        BaseADIFTestCase.setUp(self)
        self.admin_mock.createSession("testuser")
        self.reg_mgr_mock = self.corba_mock.CreateMockAnything()
        self.reg_mgr_mock.__str__ = lambda : "reg_mgr_mock"        
        self.corba_mock.StubOutWithMock(self.admin_mock, "getGroupManager") 

    def test_display_two_groups(self):
        """ Two registrar groups are displayed.
        """
        group_mgr = GroupManagerMock()
        self.admin_mock.getGroupManager().AndReturn(group_mgr)
        self.corba_mock.StubOutWithMock(group_mgr, "getGroups")
        group_mgr.getGroups().AndReturn(
            [Registry.Registrar.Group.GroupData(
                1, "test_group_1", ccReg.DateType(0, 0, 0)),
            Registry.Registrar.Group.GroupData(
                3, "test_group_3", ccReg.DateType(20, 10, 2009)),
            Registry.Registrar.Group.GroupData(
                2, "test_group_2", ccReg.DateType(0, 0, 0))])

        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/group")
        twill.commands.showforms()
        twill.commands.code(200)
        twill.commands.find(
            '''<input title="test_group_1" type="text" name="groups-0-name"'''
            ''' value="test_group_1" />''')
        twill.commands.find(
            '''<input title="test_group_2" type="text" name="groups-1-name"'''
            ''' value="test_group_2" />''')

    def test_display_zero_groups(self):
        """ Two registrar groups are displayed.
        """
        group_mgr = GroupManagerMock()
        self.admin_mock.getGroupManager().AndReturn(group_mgr)
        self.corba_mock.StubOutWithMock(group_mgr, "getGroups")
        group_mgr.getGroups().AndReturn([])

        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/group")
        twill.commands.showforms()
        twill.commands.code(200)
        twill.commands.find(
            '''<input type="text" name="groups-0-name" value="" />''')
            
    def test_delete_group(self):
        """ Two registrar groups are displayed, one gets deleted.
        """
        group_mgr = GroupManagerMock()
        self.admin_mock.getGroupManager().AndReturn(group_mgr)
        self.corba_mock.StubOutWithMock(group_mgr, "getGroups")
        group_mgr.getGroups().AndReturn(
            [Registry.Registrar.Group.GroupData(
                1, "test_group_1", ccReg.DateType(0, 0, 0)),
            Registry.Registrar.Group.GroupData(
                2, "test_group_2", ccReg.DateType(0, 0, 0))])

        self.admin_mock.getGroupManager().AndReturn(group_mgr)
        group_mgr.getGroups().AndReturn(
            [Registry.Registrar.Group.GroupData(
                1, "test_group_1", ccReg.DateType(0, 0, 0)),
            Registry.Registrar.Group.GroupData(
                2, "test_group_2", ccReg.DateType(0, 0, 0))])

        self.admin_mock.getGroupManager().AndReturn(group_mgr)
        self.corba_mock.StubOutWithMock(group_mgr, "deleteGroup")
        group_mgr.deleteGroup(1)

        self.admin_mock.getGroupManager().AndReturn(group_mgr)
        group_mgr.getGroups().AndReturn(
            [Registry.Registrar.Group.GroupData(
                2, "test_group_2", ccReg.DateType(0, 0, 0)),
            Registry.Registrar.Group.GroupData(
                1, "test_group_1", ccReg.DateType(20, 10, 2009))])
        self.admin_mock.getGroupManager().AndReturn(group_mgr)
        self.admin_mock.getGroupManager().AndReturn(group_mgr)

        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/group")
        twill.commands.showforms()
        twill.commands.code(200)
        twill.commands.fv(2, "groups-0-DELETE", "1")
        twill.commands.submit()

        twill.commands.showforms()
        twill.commands.code(200)
        twill.commands.notfind(
            '''<input title="test_group_1" type="text" name="groups-0-name"'''
            ''' value="test_group_1" />''')
        twill.commands.find(
            '''<input title="test_group_2" type="text" name="groups-0-name"'''
            ''' value="test_group_2" />''')

    def test_delete_nonempty_group(self):
        """ Nonempty group cannot be deleted.
        """
        group_mgr = GroupManagerMock()
        self.admin_mock.getGroupManager().AndReturn(group_mgr)
        self.corba_mock.StubOutWithMock(group_mgr, "getGroups")
        group_mgr.getGroups().AndReturn(
            [Registry.Registrar.Group.GroupData(
                1, "test_group_1", ccReg.DateType(0, 0, 0)),
            Registry.Registrar.Group.GroupData(
                2, "test_group_2", ccReg.DateType(0, 0, 0))])

        self.admin_mock.getGroupManager().AndReturn(group_mgr)
        group_mgr.getGroups().AndReturn(
            [Registry.Registrar.Group.GroupData(
                1, "test_group_1", ccReg.DateType(0, 0, 0)),
            Registry.Registrar.Group.GroupData(
                2, "test_group_2", ccReg.DateType(0, 0, 0))])

        self.admin_mock.getGroupManager().AndReturn(group_mgr)
        self.corba_mock.StubOutWithMock(group_mgr, "deleteGroup")
        group_mgr.deleteGroup(1).AndRaise(
            Registry.Registrar.InvalidValue(
                "Test message that group is nonempty."))

        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/group")
        twill.commands.showforms()
        twill.commands.code(200)
        twill.commands.fv(2, "groups-0-DELETE", "1")
        twill.commands.submit()

        twill.commands.showforms()
        twill.commands.code(200)
        twill.commands.find(
            '''<input title="test_group_1" type="text" name="groups-0-name"'''
            ''' value="test_group_1" />''')


