from datetime import timedelta, datetime

from omniORB.any import to_any

from fred_webadmin.corba import Registry, ccReg
from fred_webadmin.corbarecoder import u2c, datetime_to_corba


def hist_rec(value, _from=None, to=None):
    ''' Creates history record list'''
    if _from is None:
        _from = u2c(datetime.today() - timedelta(1))
    else:
        _from = u2c(_from)

    if to is None:
        to = datetime_to_corba(None)

    return [Registry.HistoryRecord(value=to_any(value), requestId=1L, _from=_from, to=to)]


class CorbaDetailMaker(object):
    def state(self, state_id):
        return Registry.State(id=state_id, linked=[],
                              _from=ccReg.DateTimeType(date=ccReg.DateType(day=1, month=10, year=2013), hour=16, minute=45, second=5),
                              to=ccReg.DateTimeType(date=ccReg.DateType(day=0, month=0, year=0), hour=0, minute=0, second=0))

    def domain(self, handle, states_ids=None):
        if states_ids == None:
            states = []
        else:
            states = [self.state(state_id) for state_id in states_ids]

        return to_any(Registry.Domain.Detail(
            id=1L, handle=handle, roid='D001-CZ',
            registrar=hist_rec(Registry.OID(id=1L, handle='REG-FRED_A', type=ccReg.FT_REGISTRAR)),
            createDate='01.10.2013 16:45:05', transferDate='', updateDate='',
            deleteDate='01.12.2014 00:00:00', outZoneDate='31.10.2014 00:00:00',
            createRegistrar=Registry.OID(id=1L, handle='REG-FRED_A', type=ccReg.FT_REGISTRAR),
            updateRegistrar=Registry.OID(id=0L, handle='', type=ccReg.FT_REGISTRAR),
            authInfo=hist_rec('kWxeUNoi'),
            registrant=hist_rec(Registry.OID(id=1L, handle='KONTAKT', type=ccReg.FT_CONTACT)),
            expirationDate=hist_rec('01.10.2014'),
            valExDate=hist_rec(''),
            publish=hist_rec(False),
            nsset=hist_rec(Registry.OID(id=0L, handle='', type=ccReg.FT_NSSET)),
            keyset=hist_rec(Registry.OID(id=0L, handle='', type=ccReg.FT_KEYSET)),
            admins=hist_rec([]),
            temps=hist_rec([]),
            states=states
        ))

    def contact(self, handle):
        return to_any(Registry.Contact.Detail(
            id=2L, handle=handle, roid='D002-CZ',
            registrar=hist_rec(Registry.OID(id=1L, handle='REG-FRED_A', type=ccReg.FT_REGISTRAR)),
            createDate='09.10.2013 09:03:06', transferDate='', updateDate='', deleteDate='',
            createRegistrar=Registry.OID(id=1L, handle='REG-FRED_A', type=ccReg.FT_REGISTRAR),
            updateRegistrar=Registry.OID(id=0L, handle='', type=ccReg.FT_REGISTRAR),
            authInfo=hist_rec('nuziQokV'),
            name=hist_rec('Arlen Bales'),
            organization=hist_rec(''),
            street1=hist_rec('No street'),
            street2=hist_rec(''),
            street3=hist_rec(''),
            province=hist_rec(''),
            postalcode=hist_rec('12345'),
            city=hist_rec('Tibbet\'s Brook'),
            country=hist_rec('CZ'),
            telephone=hist_rec('arlen.bales@nic.cz'),
            fax=hist_rec(''),
            email=hist_rec(''),
            notifyEmail=hist_rec(''),
            ident=hist_rec(''),
            identType=hist_rec('EMPTY'),
            vat=hist_rec(''),
            discloseName=hist_rec(True),
            discloseOrganization=hist_rec(True),
            discloseEmail=hist_rec(True),
            discloseAddress=hist_rec(True),
            discloseTelephone=hist_rec(True),
            discloseFax=hist_rec(True),
            discloseIdent=hist_rec(True),
            discloseVat=hist_rec(True),
            discloseNotifyEmail=hist_rec(True),
            addresses=hist_rec([]),
            states=[]
        ))

    def registrar(self, handle):
        return to_any(Registry.Registrar.Detail(
            id=1L, ico='', dic='', varSymb='12345     ', vat=True,
            handle=handle, name='Company A l.t.d', organization='Testing registrar A',
            street1='', street2='', street3='', city='', stateorprovince='', postalcode='', country='CZ',
            telephone='', fax='', email='kuk@nic.cz', url='www.nic.cz',
            credit='478456.78', unspec_credit='0.00',
            access=[Registry.Registrar.EPPAccess(password='passwd',
                                                 md5Cert='6A:AC:49:24:F8:32:1E:B7:A1:83:B5:D4:CB:74:29:98')],
            zones=[Registry.Registrar.ZoneAccess(id=1L, name='0.2.4.e164.arpa', credit='103696.18',
                                                 fromDate=ccReg.DateType(day=1, month=1, year=2007),
                                                 toDate=ccReg.DateType(day=0, month=0, year=0)),
                   Registry.Registrar.ZoneAccess(id=2L, name='cz', credit='374760.60',
                                                 fromDate=ccReg.DateType(day=1, month=1, year=2007),
                                                 toDate=ccReg.DateType(day=0, month=0, year=0))],
            hidden=False
        ))
