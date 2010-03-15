import mox
import CORBA
import cherrypy
import twill
import datetime
import ldap

from nose import with_setup
from StringIO import StringIO
import twill.commands

from fred_webadmin import ldap_auth, corba_auth

import tests.webadmin.base as base
import fred_webadmin.controller.adif

from fred_webadmin.corba import Registry, ccReg
import fred_webadmin.logger.dummylogger as logger
from logging import error

class BaseADIFTestCase(base.DaphneTestCase):
    def setUp(self):
        base.DaphneTestCase.setUp(self)
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


class TestADIF(BaseADIFTestCase):
    def setUp(self):
        BaseADIFTestCase.setUp(self)
        # Corba objects requested from server at login time.
        self.corba_objs_created_at_login = (
            ("Admin", self.admin_mock), ("Logger", logger.DummyLogger()), 
            ("Mailer", None), ("FileManager", None))
   
    def test_login_valid_corba_auth(self):
        """ Login passes when using valid corba authentication.
        """
        fred_webadmin.config.auth_method = 'CORBA'
        # Replace fred_webadmin.controller.adif.auth module with CORBA
        # module.
        self.monkey_patch(
            fred_webadmin.controller.adif, 'auth', corba_auth)
        self.corba_conn_mock.connect("localhost_test", "fredtest")
        # Create corba objects in any order (prevent boilerplate code).
        for obj, ret in self.corba_objs_created_at_login:
            self.corba_conn_mock.getObject(obj, obj).InAnyOrder("corba_obj").AndReturn(ret)
        self.admin_mock.authenticateUser("test", "test pwd")
        self.admin_mock.createSession("test").AndReturn(self.corba_session_mock)
        self.corba_session_mock.getUser().AndReturn(self.corba_user_mock)
        self.corba_session_mock.setHistory(False)
        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/login")
        twill.commands.showforms()
        twill.commands.fv(1, "login", "test")
        twill.commands.fv(1, "password", "test pwd")
        twill.commands.fv(1, "corba_server", "0")
        twill.commands.submit()
        twill.commands.url("http://localhost:8080/summary/")
        twill.commands.code(200)

    def test_login_invalid_corba_auth(self):
        """ Login fails when using invalid corba authentication.
        """
        fred_webadmin.config.auth_method = 'CORBA'
        self.corba_conn_mock.connect("localhost_test", "fredtest")
        # Create corba objects in any order (prevent boilerplate code).
        for obj, ret in self.corba_objs_created_at_login:
            self.corba_conn_mock.getObject(obj, obj).InAnyOrder("corba_obj").AndReturn(ret)
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
            fred_webadmin.ldap_auth.ldap, 'open', self.ldap_mock)
        self.corba_conn_mock.connect("localhost_test", "fredtest")
        # Create corba objects in any order (prevent boilerplate code).
        for obj, ret in self.corba_objs_created_at_login:
            self.corba_conn_mock.getObject(obj, obj).InAnyOrder(
                "corba_obj").AndReturn(ret)
        fred_webadmin.ldap_auth.ldap.open.__call__(
            "test ldap server").AndReturn(self.ldap_mock)
        self.ldap_mock.simple_bind_s("test ldap scope test", "test pwd")
        self.admin_mock.createSession("test").AndReturn(self.corba_session_mock)
        self.corba_session_mock.getUser().AndReturn(self.corba_user_mock)
        self.corba_session_mock.setHistory(False)
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
            fred_webadmin.ldap_auth.ldap, 'open', self.ldap_mock)
        self.corba_conn_mock.connect("localhost_test", "fredtest")
        # Create corba objects in any order (prevent boilerplate code).
        for obj, ret in self.corba_objs_created_at_login:
            self.corba_conn_mock.getObject(obj, obj).InAnyOrder(
                "corba_obj").AndReturn(ret)
        fred_webadmin.ldap_auth.ldap.open.__call__(
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
            fred_webadmin.ldap_auth.ldap, 'open', self.ldap_mock)
        self.corba_conn_mock.connect("localhost_test", "fredtest")
        # Create corba objects in any order (prevent boilerplate code).
        for obj, ret in self.corba_objs_created_at_login:
            self.corba_conn_mock.getObject(obj, obj).InAnyOrder(
                "corba_obj").AndReturn(ret)
        fred_webadmin.ldap_auth.ldap.open.__call__(
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


class TestRegistrar(BaseADIFTestCase):
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

    def test_edit_correct_args(self):
        """ Registrar editation passes. """
        def _get_reg_detail():
            return self.corba_session_mock.getDetail(
                ccReg.FT_REGISTRAR, 42).AndReturn(
                    self._fabricate_registrar())
        self.admin_mock.getCountryDescList().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.admin_mock.getDefaultCountry().AndReturn(1)
        _get_reg_detail() # Display the detail.
        _get_reg_detail() # Page reloaded after clicking 'save'.
        self.admin_mock.getCountryDescList().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.corba_session_mock.updateRegistrar(
            mox.IsA(Registry.Registrar.Detail)).AndReturn(42)
        _get_reg_detail() # Jump to detail after updating.

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
        def _get_reg_detail():
            return self.corba_session_mock.getDetail(
                ccReg.FT_REGISTRAR, 42).AndReturn(
                    self._fabricate_registrar())
        self.admin_mock.getCountryDescList().InAnyOrder().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        _get_reg_detail()
        _get_reg_detail()
        self.admin_mock.getCountryDescList().InAnyOrder().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        self.corba_session_mock.updateRegistrar(
            mox.IsA(Registry.Registrar.Detail)).AndReturn(42)
        _get_reg_detail()

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
        """ Registrar creation passes. """
        self.admin_mock.getCountryDescList().InAnyOrder().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        self.admin_mock.getCountryDescList().InAnyOrder().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.corba_session_mock.updateRegistrar(
            mox.IsA(ccReg.Registrar)).AndReturn(42)
        self.corba_session_mock.getDetail(ccReg.FT_REGISTRAR, 42).AndReturn(
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
        twill.commands.submit()

        # Test that we've jumped to the detail page (i.e., creation has
        # completed successfully).
        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/registrar/detail/\?id=42")
        twill.commands.find("test handle")

    def test_create_registrar_zone_to_date_smaller_than_zone_from_date(self):
        """ Registrar creation fails when zone 'To' date is smaller than zone
            'From' date (ticket #3530)."""
        self.admin_mock.getCountryDescList().InAnyOrder().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        self.admin_mock.getCountryDescList().InAnyOrder().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.corba_session_mock.updateRegistrar(
            mox.IsA(ccReg.Registrar)).AndReturn(42)
        self.corba_session_mock.getDetail(ccReg.FT_REGISTRAR, 42).AndReturn(
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
        self.admin_mock.getDefaultCountry().AndReturn(1)

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
        self.admin_mock.getCountryDescList().InAnyOrder().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        self.admin_mock.getCountryDescList().InAnyOrder().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.corba_session_mock.updateRegistrar(
            mox.IsA(ccReg.Registrar)).AndReturn(42)
        self.corba_session_mock.getDetail(ccReg.FT_REGISTRAR, 42).AndReturn(
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
        self.admin_mock.getDefaultCountry().AndReturn(1)

        self.corba_mock.ReplayAll()

        # Create the registrar.
        twill.commands.go("http://localhost:8080/registrar/create")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        # Fill in the zone name (mandatory field).
        twill.commands.fv(2, "zones-0-name", "test zone")
        # 'To' date is bigger than 'From' date.
        twill.commands.fv(2, "zones-0-fromDate", "2011-02-01")
        twill.commands.fv(2, "zones-0-toDate", "2011-02-10")
        twill.commands.submit()

        # Test that we've jumped to the detail page (i.e., creation has
        # completed successfully).
        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/registrar/detail/\?id=42")
        twill.commands.find("test handle")


    def test_create_two_registrars_with_same_name(self):
        """ Creating second registrar with the same name fails.
            Ticket #3079. """
        self.admin_mock.getCountryDescList().InAnyOrder().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        self.admin_mock.getCountryDescList().InAnyOrder().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.corba_session_mock.updateRegistrar(
            mox.IsA(ccReg.Registrar)).AndReturn(42)
        self.corba_session_mock.getDetail(ccReg.FT_REGISTRAR, 42).AndReturn(
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
        self.admin_mock.getCountryDescList().InAnyOrder().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        self.admin_mock.getCountryDescList().InAnyOrder().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.corba_session_mock.updateRegistrar(
            mox.IsA(ccReg.Registrar)).AndRaise(ccReg.Admin.UpdateFailed)
        self.admin_mock.getDefaultCountry().AndReturn(1)

        self.corba_mock.ReplayAll()

        twill.commands.go("http://localhost:8080/registrar/create")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.submit()

        # Test that we've stayed at the 'create' page (i.e., creation has
        # failed).
        twill.commands.url("http://localhost:8080/registrar/create")


class TestBankStatement(BaseADIFTestCase):
    def _fabricate_bank_statement_detail(self):
        """ Create a fake Registry.Banking.BankItem.Detail object for testing
            purposes. """
        return CORBA.Any(
                CORBA.TypeCode("IDL:Registry/Banking/BankItem/Detail:1.0"),
                Registry.Banking.BankItem.Detail(
                    id=16319L, statementId=5106L, accountNumber='756', 
                    bankCodeId='2400', code=2, type=2, konstSym='598', 
                    varSymb='', specSymb='', price='1.62', 
                    accountEvid='07-14-2-756/2400', accountDate='31.07.2007',
                    accountMemo='Urok 07/2007', invoiceId=0L, 
                    accountName='CZ.NIC, z.s.p.o.', 
                    crTime='31.07.2007 02:00:00'))

    def test_successfull_statementitem_payment_pairing(self):
        """ Payment pairing works OK when correct registrar handle 
            is specified. """
        self.admin_mock.getCountryDescList().InAnyOrder().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        statement = self._fabricate_bank_statement_detail()
        self.corba_session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement)
        invoicing_mock = self.corba_mock.CreateMockAnything()
        self.corba_session_mock.getBankingInvoicing().AndReturn(invoicing_mock)
        invoicing_mock.pairPaymentRegistrarHandle(
            42, "test handle").AndReturn(True)
        # Create a new bank statement detail with a non-zero invoiceId value 
        # to simulate successfull payment pairing.
        statement_after_pairing = self._fabricate_bank_statement_detail()
        statement_after_pairing.value().invoiceId = 11L
        self.corba_session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement_after_pairing)

        self.corba_mock.ReplayAll()

        # Go to the pairing form 
        twill.commands.go("http://localhost:8080/bankstatement/detail/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/bankstatement/detail/\?id=42")
        # Check that we display a link to the invoice after a successfull
        # payment.
        twill.commands.find("""<a href="/invoice/detail/\?id=11">.*</a>""")

    def test_statementitem_detail_unknown_unempty_handle(self):
        """ Pairing with unknown registrar handle fails.
        """
        self.admin_mock.getCountryDescList().InAnyOrder().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        statement = self._fabricate_bank_statement_detail()
        self.corba_session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement)
        invoicing_mock = self.corba_mock.CreateMockAnything()
        self.corba_session_mock.getBankingInvoicing().AndReturn(invoicing_mock)
        invoicing_mock.pairPaymentRegistrarHandle(
            42, "test handle").AndReturn(False)
        self.corba_session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement)

        self.corba_mock.ReplayAll()

        # Go to the pairing form 
        twill.commands.go("http://localhost:8080/bankstatement/detail/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/bankstatement/detail/\?id=42")
        # Check that we do not display a link to the invoice after an 
        # unsuccessful payment attempt.
        twill.commands.notfind("""<a href="/invoice/detail/\?id=11">.*</a>""")

    def test_statementitem_detail_empty_handle(self):
        """ Pairing payment with empty registrar handle fails.
        """
        self.admin_mock.getCountryDescList().InAnyOrder().AndReturn(
            [ccReg.CountryDesc(1, 'cz')])
        self.admin_mock.getDefaultCountry().InAnyOrder().AndReturn(1)
        statement = self._fabricate_bank_statement_detail()
        self.corba_session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement)
        invoicing_mock = self.corba_mock.CreateMockAnything()
        self.corba_session_mock.getBankingInvoicing().AndReturn(invoicing_mock)
        invoicing_mock.pairPaymentRegistrarHandle(
            42, "test handle").AndReturn(False)
        self.corba_session_mock.getDetail(
            ccReg.FT_STATEMENTITEM, 42).AndReturn(statement)

        self.corba_mock.ReplayAll()

        # Go to the pairing form 
        twill.commands.go("http://localhost:8080/bankstatement/detail/?id=42")
        twill.commands.showforms()
        twill.commands.fv(2, "handle", "test handle")
        twill.commands.submit()

        twill.commands.code(200)
        twill.commands.url("http://localhost:8080/bankstatement/detail/\?id=42")
        # Check that we do not display a link to the invoice after
        #an unsuccessful payment attempt.
        twill.commands.notfind("""<a href="/invoice/detail/\?id=11">.*</a>""")


class TestLoggerNoLogView(BaseADIFTestCase):
    def setUpConfig(self):
        fred_webadmin.config.auth_method = 'CORBA'
        fred_webadmin.config.audit_log['viewing_actions_enabled'] = False
        fred_webadmin.config.audit_log['logging_actions_enabled'] = False
        fred_webadmin.config.audit_log['force_critical_logging'] = False

    def setUp(self):
        self.setUpConfig()
        BaseADIFTestCase.setUp(self)
        # Corba objects requested from server at login time.
        self.corba_objs_created_at_login = (
            ("Admin", self.admin_mock), ("Mailer", None), 
            ("FileManager", None))

    def test_logger_hidden_when_log_view_is_disabled_in_config(self):
        # Replace fred_webadmin.controller.adif.auth module with CORBA
        # module.
        self.monkey_patch(
            fred_webadmin.controller.adif, 'auth', corba_auth)
        self.monkey_patch(
            fred_webadmin.controller.adif, 'SessionLogger',
            fred_webadmin.logger.dummylogger.DummyLogger)
        self.monkey_patch(
            fred_webadmin.controller.adif, 'SessionLoggerFailSilent',
            fred_webadmin.logger.dummylogger.DummyLogger)
        self.monkey_patch(
            fred_webadmin.controller.adif, 'auth', corba_auth)
        self.corba_conn_mock.connect("localhost_test", "fredtest")
        # Create corba objects in any order (prevent boilerplate code).
        for obj, ret in self.corba_objs_created_at_login:
            self.corba_conn_mock.getObject(obj, obj).InAnyOrder("corba_obj").AndReturn(ret)
        self.admin_mock.authenticateUser("test", "test pwd")
        self.admin_mock.createSession("test").AndReturn(self.corba_session_mock)
        self.corba_session_mock.getUser().AndReturn(self.corba_user_mock)
        self.corba_session_mock.setHistory(False)

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

        self.corba_mock.VerifyAll()


class TestLoggerLogView(BaseADIFTestCase):
    def setUpConfig(self):
        fred_webadmin.config.auth_method = 'CORBA'
        fred_webadmin.config.audit_log['viewing_actions_enabled'] = True
    
