import mox
import CORBA
import cherrypy
import twill
import datetime

from StringIO import StringIO
import twill.commands

import tests.webadmin.base as base
import fred_webadmin.controller.adif

from fred_webadmin.corba import Registry, ccReg


class TestADIF(base.DaphneTestCase):
    def setUp(self):
        base.DaphneTestCase.setUp(self)
        # Create the application, mount it and start the server.
        root = fred_webadmin.controller.adif.ADIF()
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

    def test_login(self):
        pass


class TestRegistrar(base.DaphneTestCase):
    def setUp(self):
        base.DaphneTestCase.setUp(self)
        cherrypy.config.update({ "server.logToScreen" : False })
        cherrypy.config.update({'log.screen': False})

        root = fred_webadmin.controller.adif.ADIF()
        root.registrar = fred_webadmin.controller.adif.Registrar()
        wsgiApp = cherrypy.tree.mount(root)
        cherrypy.server.start()
        twill.add_wsgi_intercept('localhost', 8080, lambda : wsgiApp)
        
        self.outp = StringIO()
        twill.set_output(self.outp)

    def tearDown(self):
        base.DaphneTestCase.tearDown(self)
        # remove intercept.
        twill.remove_wsgi_intercept('localhost', 8080) 
        # shut down the cherrypy server.
        cherrypy.server.stop()

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

    def test_create_registrar_zone_to_date_smaller_than_zone_from_date(self):
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
        twill.commands.fv(2, "zones-0-fromDate", "2010-02-01")
        twill.commands.fv(2, "zones-0-toDate", "2010-02-10")
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


class TestBankStatement(base.DaphneTestCase):
    def setUp(self):
        base.DaphneTestCase.setUp(self)
        root = fred_webadmin.controller.adif.ADIF()
        root.bankstatement = fred_webadmin.controller.adif.BankStatement()
        wsgiApp = cherrypy.tree.mount(root)
        cherrypy.config.update({ "server.logToScreen" : False })
        cherrypy.server.start()
        twill.add_wsgi_intercept('localhost', 8080, lambda : wsgiApp)
        
        self.outp = StringIO()
        twill.set_output(self.outp)

    def tearDown(self):
        base.DaphneTestCase.tearDown(self)
        # Remove intercept.
        twill.remove_wsgi_intercept('localhost', 8080)
        # Stop the server.
        cherrypy.server.stop()

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
