from fred_webadmin.corba import ccReg, Registry
from achoo import calling, requiring
import fred_webadmin.corbarecoder as recoder
import datetime

"""
    Note: These tests are an example of the ugly mirror testing anti pattern.
    (http://jasonrudolph.com/blog/2008/07/30/testing-anti-patterns-the-ugly-mirror/)

    But I didn't know how to write them better, because, hey, we're mesing with Corba
    in Python here.
"""

class TestDaphneCorbaRecoder(object):
    def test_create(self):
        """ DaphneCorbaRecoder is created with supported encoding. """
        rec = recoder.DaphneCorbaRecode("utf-8")
        requiring(rec).is_not_none()

    def test_create(self):
        """ DaphneCorbaRecoder raises error for unsupported encoding. """
        calling(recoder.DaphneCorbaRecode).\
            passing("invalid coding").\
            raises(recoder.UnsupportedEncodingError)

    def test_decode(self):
        """ DaphneCorbaRecoder decodes corba entity to python correctly . """
        rec = recoder.DaphneCorbaRecode("utf-8")
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
        """ DaphneCorbaRecoder raises ValueError for an inconvertible entity. """
        rec = recoder.DaphneCorbaRecode("utf-8")
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
        rec = recoder.DaphneCorbaRecode("utf-8")
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

    def test_encode_date(self):
        rec = recoder.DaphneCorbaRecode("utf-8")
        p_obj = datetime.date(1,2,3)
        expected = ccReg.DateType(3,2,1)
        res = rec.encode(p_obj)

        requiring(res).is_not_none()
        requiring(res.__dict__).equal_to(expected.__dict__)

    def test_decode_date_type(self):
        rec = recoder.DaphneCorbaRecode("utf-8")

        d = ccReg.DateType(10,10,2009)
        res = rec.decode(d)

        requiring(res).is_not_none()
        requiring(res).equal_to(datetime.date(2009, 10, 10))

    def test_encode_nested_date(self):
        rec = recoder.DaphneCorbaRecode("utf-8")

        entity = Registry.Registrar.Detail(
            id=19, ico=u'', dic=u'', varSymb=u'', vat=False, 
            handle=u'NEW REG', name=u'name 1', organization=u'', street1=u'', 
            street2=u'', street3=u'', city=u'', stateorprovince=u'state', 
            postalcode=u'', country=u'CZ', telephone=u'', fax=u'', email=u'', 
            url=u'', credit=u'0.00', access=[], 
            zones=[
                ccReg.ZoneAccess(
                    id=0, name=u'cz', fromDate=datetime.date(2009, 12, 11), 
                    toDate=u'')],
            hidden=False)
        expected = Registry.Registrar.Detail(
            id=19, ico='', dic='', varSymb='', vat=False, handle='NEW REG', 
            name='name 1', organization='', street1='', street2='', 
            street3='', city='', stateorprovince='state', 
            postalcode='', country='CZ', telephone='', fax='', 
            email='', url='', credit='0.00', access=[], 
            zones=[
                ccReg.ZoneAccess(
                    id=0, name='cz', fromDate=ccReg.DateType(
                        day=11, month=12, year=2009), 
                    toDate='')], 
            hidden=False)
        res = rec.encode(entity)

        requiring(res).is_not_none()
        requiring(expected.__dict__['zones'][0].fromDate.__dict__).\
            equal_to(res.__dict__['zones'][0].fromDate.__dict__)

    def test_sanity(self):
        """ encode(decode(obj)) is equal to obj. """
        rec = recoder.DaphneCorbaRecode("utf-8")
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

    def test_encode_is_idempotent(self):
        #TODO(tom): write the test.
        pass
