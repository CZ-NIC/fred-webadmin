# -*- coding: utf-8 -*

from mock import Mock, call, patch
from nose.tools import assert_equal #@UnresolvedImport pylint: disable=E0611
from omniORB import CORBA
import cherrypy
import datetime
from logging import error
try:
    import ldap
except ImportError:
    error("Could not import ldap, some test will probably fail...")

from StringIO import StringIO
import twill.commands

try:
    from fred_webadmin.auth import ldap_auth, corba_auth
except Exception: # pylint: disable=W0703
    error("Could not import auth module, some test will probably fail...")

from fred_webadmin.tests.webadmin.base import DaphneTestCase
import fred_webadmin.controller.adif
import fred_webadmin.webwidgets.forms

from fred_webadmin.corba import Registry, ccReg
import pylogger.dummylogger as logger
import fred_webadmin.user as fred_webadmin_user



class BaseADIFTestCase(DaphneTestCase):
    def setUp(self):
        super(BaseADIFTestCase, self).setUp()
        self.admin_mock = AdminMock()
        self.web_session_mock['Admin'] = self.admin_mock
        self.web_session_mock['user'] = fred_webadmin_user.User(UserMock())
        self.file_mgr_mock = Mock()
        self.web_session_mock['FileManager'] = self.file_mgr_mock
        self.corba_conn_mock = CorbaConnectionMock(admin=self.admin_mock)
        self.monkey_patch(
            fred_webadmin.controller.adif, 'corba_obj', self.corba_conn_mock)
        # Create the application, mount it and start the server.
        root = fred_webadmin.controller.adif.prepare_root()
        wsgiApp = cherrypy.tree.mount(root)
        cherrypy.config.update({'server.socket_host': '0.0.0.0',
                                 'server.socket_port': 9090,
                                                         })
        cherrypy.server.start()
        # Redirect HTTP requests.
        twill.add_wsgi_intercept('localhost', 8080, lambda : wsgiApp)
        # Keep Twill quiet (suppress normal Twill output).
        self.outp = StringIO()
        twill.set_output(self.outp)

    def tearDown(self):
        super(BaseADIFTestCase, self).tearDown()
        # Remove the intercept.
        twill.remove_wsgi_intercept('localhost', 8080)
        # Shut down Cherrypy server.
        cherrypy.server.stop()


# pylint: disable=W0613
class GroupManagerMock(object):
    def getGroups(self):
        return [
            Registry.Registrar.Group.GroupData(
                1, "test_group_1", ccReg.DateType(0, 0, 0)),
            Registry.Registrar.Group.GroupData(
                10, "test_group_2", ccReg.DateType(20, 10, 2009)),
            Registry.Registrar.Group.GroupData(
                7, "test_group_3", ccReg.DateType(0, 0, 0))]

    def getMembershipsByRegistar(self, reg_id):
        return []

    def deleteGroup(self, group_id):
        pass

    def addRegistrarToGroup(self, reg_id, group_id):
        pass

    def removeRegistrarFromGroup(self, reg_id, group_id):
        pass

    def updateGroup(self, group_id, name):
        pass


class CertificationManagerMock(object):
    def __init__(self):
        super(CertificationManagerMock, self).__init__()

    def getCertificationsByRegistrar(self, reg_id):
        return []
        # [Registry.Registrar.Certification.CertificationData(
        #    1, ccReg.DateType(1, 1, 2008), ccReg.DateType(1, 1, 2010), 2, 17)]

    def createCertification(self, reg_id, from_date, to_date, score, file_id):
        return 17

    def updateCertification(self, crt_id, score, file_id):
        pass

    def shortenCertification(self, crt_id, to_date):
        pass


class AdminMock(object):
    def __init__(self):
        super(AdminMock, self).__init__()
        self.session = None
        self.group_manager_mock = GroupManagerMock() # helper reference to GrouManagerMock
        self.certification_manager_mock = CertificationManagerMock()

    def getCountryDescList(self):
        return [Registry.CountryDesc(1, 'cz')]

    def getDefaultCountry(self):
        return 1

    def getGroupManager(self):
        return self.group_manager_mock

    def getCertificationManager(self):
        return self.certification_manager_mock

    def createSession(self, username):
        self.session = Mock()
        self.session.getUser.return_value = UserMock()
        return "testSessionString"

    def getSession(self, session_str):
        return self.session

    def authenticateUser(self, user, pwd):
        pass

    def isRegistrarBlocked(self, reg_id):
        return False


class CorbaConnectionMock(object):
    def __init__(self, admin=AdminMock(), logger_obj=logger.DummyLogger(), mailer=None, filemgr=None, messages=None):
        super(CorbaConnectionMock, self).__init__()
        self.obj = {
            "ccReg.Admin": admin,
            "ccReg.Logger": logger_obj,
            "ccReg.Mailer": mailer,
            "ccReg.FileManager": filemgr,
            "Registry.Messages": messages,
        }

    def getObject(self, obj1, obj2):
        return self.obj[obj2]

    def connect(self, user, pwd):
        pass


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
# pylint: enable=W0613


class TestADIFAuthentication(BaseADIFTestCase):
    def test_login_valid_corba_auth(self):
        """ Login passes when using valid corba authentication.
        """
        fred_webadmin.config.auth_method = 'CORBA'
        # Replace fred_webadmin.controller.adif.auth module with CORBA
        # module.
        self.monkey_patch(
            fred_webadmin.controller.adif, 'auth', corba_auth)

        twill.commands.go("http://localhost:8080/login")
        twill.commands.showforms()
        twill.commands.fv(1, "login", "test")
        twill.commands.fv(1, "password", "test pwd")
        twill.commands.fv(1, "corba_server", "0")
        twill.commands.submit()
        twill.commands.url("http://localhost:8080/summary/")
        twill.commands.code(200)

#    def ignoretest_login_unicode_username(self):
#        """ Login passes when using valid corba authentication.
#            THIS IS BROKEN, probably because of strange way
#            mechanize (and twill that uses it) handles unicode strings.
#        """
#        fred_webadmin.config.auth_method = 'CORBA'
#        # Replace fred_webadmin.controller.adif.auth module with CORBA
#        # module.
#        self.monkey_patch(
#            fred_webadmin.controller.adif, 'auth', corba_auth)
#        self.corba_mock.ReplayAll()
#
#        twill.commands.go("http://localhost:8080/login")
#        twill.commands.showforms()
#        twill.commands.fv(1, "login", u"ěščěšřéýí汉语unicode")
#        twill.commands.fv(1, "password", "test pwd")
#        twill.commands.fv(1, "corba_server", "0")
#        twill.commands.submit()
#        twill.commands.url("http://localhost:8080/summary/")
#        twill.commands.code(200)

    def test_login_invalid_corba_auth(self):
        """ Login fails when using invalid corba authentication.
        """
        fred_webadmin.config.auth_method = 'CORBA'
        self.monkey_patch(
            fred_webadmin.controller.adif, 'auth', corba_auth)

        with patch.object(AdminMock, 'authenticateUser') as mocked_authenticateUser:
            mocked_authenticateUser.side_effect = ccReg.Admin.AuthFailed

            twill.commands.go("http://localhost:8080/login")
            twill.commands.showforms()
            twill.commands.fv(1, "login", "test")
            twill.commands.fv(1, "password", "test pwd")
            twill.commands.fv(1, "corba_server", "0")
            twill.commands.submit()
            twill.commands.url("http://localhost:8080/login/")
            twill.commands.code(403)

        mocked_authenticateUser.assert_called_once_with('test', 'test pwd')

    def test_double_login(self):
        """ Loging in when already loged in redirects to /summary.
        """
        self.web_session_mock['corbaSessionString'] = "test session string"
        twill.commands.go("http://localhost:8080/login/")
        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/summary/")

    def test_login_invalid_form(self):
        """ Login fails when submitting invalid form.
        """
        twill.commands.go("http://localhost:8080/login/")
        twill.commands.showforms()
        twill.commands.fv(1, "login", "")
        twill.commands.fv(1, "password", "")
        twill.commands.code(200)
        # Check that we did not leave the login page.
        twill.commands.url("http://localhost:8080/login/")

class TestADIFAuthenticationLDAP(BaseADIFTestCase):
    def setUp(self):
        super(TestADIFAuthenticationLDAP, self).setUp()
        self.monkey_patch(fred_webadmin.controller.adif, 'auth', ldap_auth)
        self.monkey_patch(fred_webadmin.config, 'auth_method', 'LDAP')
        self.monkey_patch(fred_webadmin.config, 'LDAP_scope', 'test ldap scope %s')
        self.monkey_patch(fred_webadmin.config, 'LDAP_server', 'test ldap server')
        # Mock out ldap.open method. We must not mock the whole ldap package,
        # because ldap_auth uses ldap exceptions.
        self.ldap_open_mock = Mock()
        self.monkey_patch(fred_webadmin.auth.ldap_auth.ldap, 'open', self.ldap_open_mock) #@UndefinedVariable

    def assert_ldap_called(self):
        assert_equal(self.ldap_open_mock.mock_calls, [call('test ldap server'),
                                                      call().simple_bind_s('test ldap scope test', 'test pwd')])
    def test_login_ldap_valid_credentials(self):
        """ Login passes when valid credentials are supplied when using LDAP.
        """
        twill.commands.go("http://localhost:8080/login")
        twill.commands.showforms()
        twill.commands.fv(1, "login", "test")
        twill.commands.fv(1, "password", "test pwd")
        twill.commands.fv(1, "corba_server", "0")
        twill.commands.submit()
        # Invalid credentials => stay at login page.
        twill.commands.url("http://localhost:8080/summary/")
        twill.commands.code(200)

        self.assert_ldap_called()


    def test_login_ldap_invalid_credentials(self):
        """ Login fails when invalid credentials are supplied when using LDAP.
        """
        self.ldap_open_mock.return_value.simple_bind_s.side_effect = ldap.INVALID_CREDENTIALS

        twill.commands.go("http://localhost:8080/login")
        twill.commands.showforms()
        twill.commands.fv(1, "login", "test")
        twill.commands.fv(1, "password", "test pwd")
        twill.commands.fv(1, "corba_server", "0")
        twill.commands.submit()
        # Invalid credentials => stay at login page.
        twill.commands.url("http://localhost:8080/login/")
        twill.commands.code(403)

        self.assert_ldap_called()

    def test_login_ldap_server_down(self):
        """ Login fails when using LDAP and LDAP server is down.
        """
        self.ldap_open_mock.return_value.simple_bind_s.side_effect = ldap.SERVER_DOWN

        twill.commands.go("http://localhost:8080/login")
        twill.commands.showforms()
        twill.commands.fv(1, "login", "test")
        twill.commands.fv(1, "password", "test pwd")
        twill.commands.fv(1, "corba_server", "0")
        twill.commands.submit()
        # Invalid credentials => stay at login page.
        twill.commands.url("http://localhost:8080/login/")

        self.assert_ldap_called()


class TestRegistrarBase(BaseADIFTestCase):
    def setUp(self):
        super(TestRegistrarBase, self).setUp()
        self.admin_mock.createSession('testuser')
        self.session_mock = self.admin_mock.getSession('testSessionString')
        # when called with argument 17, return this FileInfo:
        self.file_mgr_mock.info.side_effect = lambda fileinfo_id: \
            ccReg.FileInfo(1, 'testfile', 'testpath', 'testmime', 0, ccReg.DateType(10, 10, 2010), 100) \
            if fileinfo_id == 17 else None
        self.session_mock.updateRegistrar.side_effect = lambda reg: \
            42 if isinstance(reg, (ccReg.AdminRegistrar, Registry.Registrar.Detail)) else None
        self.session_mock.getDetail.side_effect = lambda ft_type, obj_id: \
            self._fabricate_registrar() if (ft_type, obj_id) == (ccReg.FT_REGISTRAR, 42) else None

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


class TestRegistrar(TestRegistrarBase):
    def test_edit_correct_args(self):
        """ Registrar editation passes. """
        twill.commands.go("http://localhost:8080/registrar/edit/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url(r"http://localhost:8080/registrar/detail/\?id=42")
        twill.commands.find("test handle")

    def test_edit_incorrect_zone_date_arg(self):
        """ Registrar editation does not pass when invalid zone date
            provided. """
        twill.commands.go("http://localhost:8080/registrar/edit/?id=42")
        twill.commands.showforms()

        twill.commands.fv(2, "handle", "test handle")
        twill.commands.fv(2, "zones-0-toDate", "test invalid date")
        twill.commands.submit()

        # Test that we stay in edit, because the form is not valid.
        twill.commands.code(200)
        twill.commands.url(r"http://localhost:8080/registrar/edit/\?id=42")

    def test_create(self):
        """ Registrar creation passes.
        """
        # Create the registrar.
        twill.commands.go("http://localhost:8080/registrar/create")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.submit()

        # Test that we've jumped to the detail page (i.e., creation has
        # completed successfully).
        twill.commands.code(200)
        twill.commands.url(r"http://localhost:8080/registrar/detail/\?id=42")
        twill.commands.find("test handle")

    def test_create_registrar_zone_to_date_smaller_than_zone_from_date(self):
        """ Registrar creation fails when zone 'To' date is smaller than zone
            'From' date (ticket #3530)."""
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
        twill.commands.find('must be bigger')

    def test_create_registrar_zone_to_date_bigger_than_zone_from_date(self):
        """ Registrar creation passes when zone 'To' date is bigger than zone
            'From' date."""
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
        twill.commands.url(r"http://localhost:8080/registrar/detail/\?id=42")
        twill.commands.find("test handle")

    def test_create_two_registrars_with_same_name(self):
        """ Creating second registrar with the same name fails.
            Ticket #3079. """
        # Create the first registrar.
        twill.commands.go("http://localhost:8080/registrar/create")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url(r"http://localhost:8080/registrar/detail/\?id=42")
        twill.commands.find("test handle")

        # Now create the second one with the same name.
        self.session_mock.updateRegistrar.side_effect = ccReg.Admin.UpdateFailed

        twill.commands.go("http://localhost:8080/registrar/create")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.submit()

        # Test that we've stayed at the 'create' page (i.e., creation has
        # failed).
        twill.commands.url("http://localhost:8080/registrar/create")
        twill.commands.code(200)
        twill.commands.find('Updating registrar failed')


class TestRegistrarGroups(TestRegistrarBase):
    def test_add_registrar_to_group(self):
        twill.commands.go("http://localhost:8080/registrar/edit/?id=42")

        self.monkey_patch(self.admin_mock.group_manager_mock, 'getMembershipsByRegistar',
            lambda reg_id: [Registry.Registrar.Group.MembershipByRegistrar(1, 1,
                            ccReg.DateType(1, 1, 2008), ccReg.DateType(0, 0, 0))])

        twill.commands.showforms()
        twill.commands.fv(2, "groups-0-id", "1")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.find("test_group_1")

    def test_remove_registrar_from_group(self):
        with patch.object(self.admin_mock.group_manager_mock, 'getMembershipsByRegistar') as mock_getMembershipsByReg:
            mock_getMembershipsByReg.side_effect = \
                lambda reg_id: [Registry.Registrar.Group.MembershipByRegistrar(1, 1,
                                ccReg.DateType(1, 1, 2008), ccReg.DateType(0, 0, 0))]

            twill.commands.go("http://localhost:8080/registrar/edit/?id=42")

        # now with normal getMembershipsByRegistar method which returns empty list:

        twill.commands.showforms()
        twill.commands.fv(2, "groups-0-DELETE", "1")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.notfind("test_group_1")


class TestRegistrarCertifications(TestRegistrarBase):
    def setUp(self):
        super(TestRegistrarCertifications, self).setUp()

    def test_add_certification(self):
        """ Correctly configured certification is added.
        """
        twill.commands.go("http://localhost:8080/registrar/edit/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "certifications-0-fromDate", datetime.date.today().isoformat())
        twill.commands.fv(2, "certifications-0-toDate", (datetime.date.today() + datetime.timedelta(7)).isoformat())
        twill.commands.fv(2, "certifications-0-score", "2")
        twill.commands.formfile(2, "certifications-0-evaluation_file", "./fred_webadmin/tests/webadmin/foofile.bar")

        file_upload_mock = Mock()
        self.file_mgr_mock.save.side_effect = lambda name, mimetype, filetype: \
            file_upload_mock if name == "./fred_webadmin/tests/webadmin/foofile.bar" \
                                 and mimetype == "application/octet-stream" \
                                 and filetype == 6 \
                             else None
        file_upload_mock.finalize_upload.return_value = 17

        # Jump to detail after updating.
        get_cert_by_reg_mock = Mock()
        self.monkey_patch(self.admin_mock.certification_manager_mock, 'getCertificationsByRegistrar',
                          get_cert_by_reg_mock)
        get_cert_by_reg_mock.side_effect = [
            [], # first call return empty list
            [ # second call return CertificationData:
                Registry.Registrar.Certification.CertificationData(
                    1, ccReg.DateType(1, 1, 2008),
                    ccReg.DateType(1, 1, 2010), 2, 17)
            ]
        ]

        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url(r"http://localhost:8080/registrar/detail/\?id=42")
        twill.commands.showforms()
        twill.commands.find(r'''<a href="/file/detail/\?id=17"''')

    def test_add_certification_no_file(self):
        """ Certification is not added when no file has been uploaded.
        """
        twill.commands.go("http://localhost:8080/registrar/edit/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "certifications-0-fromDate", datetime.date.today().isoformat())
        twill.commands.fv(2, "certifications-0-toDate", (datetime.date.today() + datetime.timedelta(7)).isoformat())
        twill.commands.fv(2, "certifications-0-score", "2")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url(r"http://localhost:8080/registrar/edit/\?id=42")
        twill.commands.find('You have not specified the upload file for a certification')

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
        date_mock = TestRegistrarCertifications.DateMock
        self.monkey_patch(fred_webadmin.webwidgets.forms.editforms, 'date', date_mock)

        get_cert_by_reg_mock = Mock()
        result_1 = [Registry.Registrar.Certification.CertificationData(
                        1, ccReg.DateType(1, 1, 2008),
                        ccReg.DateType(1, 1, 2010), 2, 17)]
        # result 2 is same as 1, but must be here again, because it's converted in-place by corbarecoder
        result_2 = [Registry.Registrar.Certification.CertificationData(
                        1, ccReg.DateType(1, 1, 2008),
                        ccReg.DateType(1, 1, 2010), 2, 17)]
        result_3 = [Registry.Registrar.Certification.CertificationData(
                        1, ccReg.DateType(1, 1, 2008),
                        ccReg.DateType(12, 12, 2009), 2, 17)]
        get_cert_by_reg_mock.side_effect = [result_1, result_2, result_3]
        self.monkey_patch(self.admin_mock.certification_manager_mock, 'getCertificationsByRegistrar',
                          get_cert_by_reg_mock)

        twill.commands.go("http://localhost:8080/registrar/edit/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "certifications-0-toDate", "2009-12-12")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url(r"http://localhost:8080/registrar/detail/\?id=42")
        twill.commands.showforms()
        twill.commands.find(r'''<a href="/file/detail/\?id=17"''')
        twill.commands.find("2009-12-12")


class TestBankStatement(BaseADIFTestCase):
    def setUp(self):
        super(TestBankStatement, self).setUp()
        self.admin_mock.createSession('testuser')
        self.session_mock = self.admin_mock.getSession('testSessionString')
        self.session_mock.getDetail.side_effect = lambda ft_type, obj_id: \
            self._fabricate_bank_statement_detail() if (ft_type, obj_id) == (ccReg.FT_STATEMENTITEM, 42) else None
        self.invoicing_mock = Mock()
        self.session_mock.getBankingInvoicing.return_value = self.invoicing_mock

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
        self.invoicing_mock.pairPaymentRegistrarHandle.side_effect = lambda payment_id, reg_id: \
            True if (payment_id, reg_id) == (42, "test handle") else None
        self.invoicing_mock.setPaymentType.side_effect = lambda payment_id, payment_type: \
            True if (payment_id, payment_type) == (42, 2) else None

        # Go to the pairing form
        twill.commands.go("http://localhost:8080/bankstatement/detail/?id=42")
        # Create a new bank statement detail with a non-zero invoiceId value
        # to simulate successful payment pairing.
        statement_after_pairing = self._fabricate_bank_statement_detail()
        statement_after_pairing.value().invoiceId = 11L
        statement_after_pairing.value().type = 2
        self.session_mock.getDetail.side_effect = lambda ft_type, obj_id: \
             statement_after_pairing if (ft_type, obj_id) == (ccReg.FT_STATEMENTITEM, 42) else None

        twill.commands.fv(2, "handle", "test handle")
        twill.commands.fv(2, "type", "2")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url(r"http://localhost:8080/bankstatement/detail/\?id=42")
        # Check that we display a link to the invoice after a successful
        # payment.
        twill.commands.find(r"""<a href="/invoice/detail/\?id=11">.*</a>""")

    def test_successfull_statementitem_payment_pairing_no_reg_handle(self):
        """ Payment pairing works OK when correct registrar handle
            is not specified, but type != "from/to registrar". """
        self.invoicing_mock.setPaymentType.side_effect = lambda payment_id, payment_type: \
            True if (payment_id, payment_type) == (42, 3) else None

        # Go to the pairing form
        twill.commands.go("http://localhost:8080/bankstatement/detail/?id=42")

        # Create a new bank statement detail with a non-zero invoiceId value
        # to simulate successfull payment pairing.
        statement_after_pairing = self._fabricate_bank_statement_detail()
        statement_after_pairing.value().invoiceId = 11L
        statement_after_pairing.value().type = 3
        self.session_mock.getDetail.side_effect = lambda ft_type, obj_id: \
             statement_after_pairing if (ft_type, obj_id) == (ccReg.FT_STATEMENTITEM, 42) else None

        twill.commands.showforms()
        twill.commands.fv(2, "type", "3")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url(r"http://localhost:8080/bankstatement/detail/\?id=42")
        # Check that we do not display a link to the invoice after a successfull
        # payment (because it's not paired with a registrar).
        twill.commands.code(200)
        twill.commands.notfind(r"""<a href="/invoice/detail/\?id=11">.*</a>""")

    def test_successfull_statementitem_payment_pairing_incorrect_reg_handle(self):
        """ Payment pairing works OK when an invalid registrar handle
            is specified, but type != "from/to registrar". """
        self.invoicing_mock.setPaymentType.side_effect = lambda payment_id, payment_type: \
            True if (payment_id, payment_type) == (42, 3) else None

        # Go to the pairing form
        twill.commands.go("http://localhost:8080/bankstatement/detail/?id=42")

        # Create a new bank statement detail with a non-zero invoiceId value
        # to simulate successfull payment pairing.
        statement_after_pairing = self._fabricate_bank_statement_detail()
        statement_after_pairing.value().invoiceId = 11L
        statement_after_pairing.value().type = 3
        self.session_mock.getDetail.side_effect = lambda ft_type, obj_id: \
             statement_after_pairing if (ft_type, obj_id) == (ccReg.FT_STATEMENTITEM, 42) else None

        twill.commands.showforms()
        twill.commands.fv(2, "handle", "invalid handle")
        twill.commands.fv(2, "type", "3")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url(r"http://localhost:8080/bankstatement/detail/\?id=42")
        # Check that we do not display a link to the invoice after a successfull
        # payment (because it's not paired with a registrar).
        twill.commands.code(200)
        twill.commands.notfind(r"""<a href="/invoice/detail/\?id=11">.*</a>""")


    def test_statementitem_detail_unknown_unempty_handle(self):
        """ Pairing with unknown registrar handle fails.
        """
        self.invoicing_mock.pairPaymentRegistrarHandle.side_effect = lambda payment_id, reg_id: \
            False if (payment_id, reg_id) == (42, "test handle") else None

        # Go to the pairing form
        twill.commands.go("http://localhost:8080/bankstatement/detail/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.fv(2, "type", "2")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url(r"http://localhost:8080/bankstatement/detail/\?id=42")
        # Check that we do not display a link to the invoice after an
        # unsuccessful payment attempt.
        twill.commands.notfind(r"""<a href="/invoice/detail/\?id=11">.*</a>""")
        twill.commands.find(r"""Could not pair. Perhaps you have entered an invalid handle?""")

    def test_statementitem_detail_empty_handle(self):
        """ Pairing payment with empty registrar handle fails.
        """
        self.invoicing_mock.pairPaymentRegistrarHandle.side_effect = lambda payment_id, reg_id: \
            False if (payment_id, reg_id) == (42, "test handle") else None

        # Go to the pairing form
        twill.commands.go("http://localhost:8080/bankstatement/detail/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.fv(2, "type", "2")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url(r"http://localhost:8080/bankstatement/detail/\?id=42")
        # Check that we do not display a link to the invoice after
        # an unsuccessful payment attempt.
        twill.commands.notfind(r"""<a href="/invoice/detail/\?id=11">.*</a>""")
        twill.commands.find(r"""Could not pair. Perhaps you have entered an invalid handle?""")

    def test_statementitem_detail_no_perms_to_change_type(self):
        """ Pairing payment form is not displayed when user has no permissions to change.
        """
        with patch.object(cherrypy.session['user'], '_authorizer') as authorizer_mock:
            self.invoicing_mock.pairPaymentRegistrarHandle.side_effect = lambda payment_id, reg_id: \
                False if (payment_id, reg_id) == (42, "test handle") else None

            authorizer_mock.has_permission.side_effect = lambda obj, action: \
                True if (obj, action) == ('bankstatement', 'read') else False

            # Go to the pairing form
            twill.commands.go("http://localhost:8080/bankstatement/detail/?id=42")
            twill.commands.showforms()
            twill.commands.notfind("""<input type="text" name="handle" value=\"\"""")


class TestLoggerNoLogView(BaseADIFTestCase):
    def setUp(self):
        self.monkey_patch(fred_webadmin.config, 'debug', False)
        self.monkey_patch(fred_webadmin.config, 'auth_method', 'CORBA')
        audit_log = {
            'viewing_actions_enabled': False,
            'logging_actions_enabled': False,
            'force_critical_logging': False,
        }
        self.monkey_patch(fred_webadmin.config, 'audit_log', audit_log)
        super(TestLoggerNoLogView, self).setUp()

    def test_logger_hidden_when_log_view_is_disabled_in_config(self):
        # Replace fred_webadmin.controller.adif.auth module with CORBA
        # module.
        self.monkey_patch(
            fred_webadmin.controller.adif, 'auth', corba_auth)

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


class TestRegistrarGroupEditor(BaseADIFTestCase):
    def setUp(self):
        BaseADIFTestCase.setUp(self)
        self.reg_mgr_mock = Mock(name='reg_mgr_mock')

    def test_display_two_groups(self):
        """ Two registrar groups are displayed.
        """
        twill.commands.go("http://localhost:8080/group")
        twill.commands.showforms()
        twill.commands.code(200)

        twill.commands.find(
            '''<input title="test_group_1" type="text" name="groups-0-name"'''
            ''' value="test_group_1" />''')
        twill.commands.find(
            '''<input title="test_group_3" type="text" name="groups-1-name"'''
            ''' value="test_group_3" />''')

    def test_display_zero_groups(self):
        """ Two registrar groups are displayed.
        """
        self.monkey_patch(self.admin_mock.group_manager_mock, 'getGroups', lambda :[])

        twill.commands.go("http://localhost:8080/group")
        twill.commands.showforms()
        twill.commands.code(200)
        twill.commands.find(
            '''<input type="text" name="groups-0-name" value="" />''')

    def test_delete_group(self):
        """ Two registrar groups are displayed, one gets deleted.
        """
        self.monkey_patch(self.admin_mock.group_manager_mock, 'getGroups', lambda : \
            [Registry.Registrar.Group.GroupData(
                1, "test_group_1", ccReg.DateType(0, 0, 0)),
            Registry.Registrar.Group.GroupData(
                2, "test_group_2", ccReg.DateType(0, 0, 0))])


        twill.commands.go("http://localhost:8080/group")

        # simulate one group delete
        self.monkey_patch(self.admin_mock.group_manager_mock, 'getGroups', lambda : \
            [Registry.Registrar.Group.GroupData(
                2, "test_group_2", ccReg.DateType(0, 0, 0)),
            Registry.Registrar.Group.GroupData(
                1, "test_group_1", ccReg.DateType(20, 10, 2009))])

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
        self.monkey_patch(self.admin_mock.group_manager_mock, 'getGroups', lambda : \
            [Registry.Registrar.Group.GroupData(
                1, "test_group_1", ccReg.DateType(0, 0, 0)),
            Registry.Registrar.Group.GroupData(
                2, "test_group_2", ccReg.DateType(0, 0, 0))])

        deleteGroup_mock = Mock()
        deleteGroup_mock.side_effect = Registry.Registrar.InvalidValue("Test message that group is nonempty.")
        self.monkey_patch(self.admin_mock.group_manager_mock, 'deleteGroup', deleteGroup_mock)

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
