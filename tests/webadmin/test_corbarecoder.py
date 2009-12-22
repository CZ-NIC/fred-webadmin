from fred_webadmin.corba import ccReg, Registry
from achoo import calling, requiring
import fred_webadmin.corbarecoder as recoder
import datetime

class TestCorbaRecoder(object):
    def test_create(self):
        """ CorbaRecoder is created with supported encoding. """
        rec = recoder.CorbaRecode("utf-8")
        requiring(rec).is_not_none()

    def test_create(self):
        """ CorbaRecoder raises error for unsupported encoding. """
        calling(recoder.CorbaRecode).\
            passing("invalid coding").\
            raises(recoder.UnsupportedEncodingError)

    def test_decode(self):
        """ CorbaRecoder decodes corba entity to python correctly . """
        rec = recoder.CorbaRecode("utf-8")
        reg = Registry.Registrar.Detail(
            id=19, ico='', dic='', varSymb='',
            vat=False, handle='NEW REG', name='name 1', organization='',
            street1='', street2='', street3='', city='', stateorprovince='state',
            postalcode='', country='CZ', telephone='', fax='', email='', url='',
            credit='0.00', access=[], zones=[], hidden=False)
        expected = Registry.Registrar.Detail(
            id=19, ico=u'', dic=u'', varSymb=u'', vat=False, 
            handle=u'NEW REG', name=u'name 1', organization=u'', street1=u'', 
            street2=u'', street3=u'', city=u'', stateorprovince=u'state', 
            postalcode=u'', country=u'CZ', telephone=u'', fax=u'', email=u'', 
            url=u'', credit=u'0.00', access=[], zones=[], hidden=False)

        decoded_reg = rec.decode(reg)

        requiring(decoded_reg).is_not_none()
        requiring(decoded_reg.__dict__).equal_to(expected.__dict__)

    def test_decode_inconvertible(self):
        """ CorbaRecoder raises ValueError for an inconvertible entity. """
        rec = recoder.CorbaRecode("utf-8")
        reg = Registry.Registrar.Detail(
            id=19, ico=u'', dic=u'', varSymb=u'', vat=False, handle=u'NEW REG',
            name=u'name 1', organization=u'', street1=u'', street2=u'', 
            street3=u'', city=u'', stateorprovince=u'state', postalcode=u'', 
            country=u'CZ', telephone=u'', fax=u'', email=u'', url=u'', 
            credit=u'0.00', access=[], zones=[ccReg.ZoneAccess(id=0,
            name=u'cz', fromDate=datetime.date(2009, 12, 11), toDate=u'')],
            hidden=False)

        calling(rec.decode).passing(reg).raises(ValueError)

    def test_encode(self):
        rec = recoder.CorbaRecode("utf-8")
        python_entity = Registry.Registrar.Detail(
            id=19, ico=u'', dic=u'', varSymb=u'', vat=False, 
            handle=u'NEW REG', name=u'name 1', organization=u'', street1=u'', 
            street2=u'', street3=u'', city=u'', stateorprovince=u'state', 
            postalcode=u'', country=u'CZ', telephone=u'', fax=u'', email=u'', 
            url=u'', credit=u'0.00', access=[], zones=[], hidden=False)
        expected = Registry.Registrar.Detail(
            id=19, ico='', dic='', varSymb='',
            vat=False, handle='NEW REG', name='name 1', organization='',
            street1='', street2='', street3='', city='', stateorprovince='state',
            postalcode='', country='CZ', telephone='', fax='', email='', url='',
            credit='0.00', access=[], zones=[], hidden=False)

        encoded_entity = rec.encode(python_entity)

        requiring(encoded_entity).is_not_none()
        requiring(encoded_entity.__dict__).equal_to(expected.__dict__)

    def test_encode_inconvertible(self):
        rec = recoder.CorbaRecode("utf-8")
        python_entity = Registry.Registrar.Detail(
            id=19, ico=u'', dic=u'', varSymb=u'', vat=False, 
            handle=u'NEW REG', name=u'name 1', organization=u'', street1=u'', 
            street2=u'', street3=u'', city=u'', stateorprovince=u'state', 
            postalcode=u'', country=u'CZ', telephone=u'', fax=u'', email=u'', 
            url=u'', credit=u'0.00', access=[], zones=[ccReg.ZoneAccess(id=0,
            name=u'cz', fromDate=datetime.date(2009, 12, 11), toDate=u'')],
            hidden=False)
        calling(rec.encode).passing(python_entity).raises(ValueError)

    def test_sanity(self):
        """ encode(decode(obj)) is equal to obj. """
        rec = recoder.CorbaRecode("utf-8")
        reg = Registry.Registrar.Detail(
            id=19, ico='', dic='', varSymb='',
            vat=False, handle='NEW REG', name='name 1', organization='',
            street1='', street2='', street3='', city='', stateorprovince='state',
            postalcode='', country='CZ', telephone='', fax='', email='', url='',
            credit='0.00', access=[], zones=[], hidden=False)
        expected = Registry.Registrar.Detail(
            id=19, ico=u'', dic=u'', varSymb=u'', vat=False, 
            handle=u'NEW REG', name=u'name 1', organization=u'', street1=u'', 
            street2=u'', street3=u'', city=u'', stateorprovince=u'state', 
            postalcode=u'', country=u'CZ', telephone=u'', fax=u'', email=u'', 
            url=u'', credit=u'0.00', access=[], zones=[], hidden=False)

        decoded_reg = rec.decode(reg)
        encoded_reg = rec.encode(decoded_reg)

        requiring(encoded_reg).is_not_none()
        requiring(encoded_reg.__dict__).equal_to(reg.__dict__)
