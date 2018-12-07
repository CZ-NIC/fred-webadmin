#
# Copyright (C) 2009-2018  CZ.NIC, z. s. p. o.
#
# This file is part of FRED.
#
# FRED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FRED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FRED.  If not, see <https://www.gnu.org/licenses/>.

"""
    Note: These tests are an example of the ugly mirror testing anti pattern.
    (http://jasonrudolph.com/blog/2008/07/30/testing-anti-patterns-the-ugly-mirror/)

    But I didn't know how to write them better, because, hey, we're mesing with Corba
    in Python here.
"""

import fred_webadmin.corba as fredcorba  # import ccReg, Registry
import fred_webadmin.corbarecoder as recoder
import fred_webadmin.nulltype as fredtypes
import datetime
from nose.tools import assert_equal, assert_is_not_none, assert_raises  # @UnresolvedImport pylint: disable = E0611


class Patched_datetype(fredcorba.ccReg.DateType):
    def __init__(self, day=0, month=0, year=0):
        self.day, self.month, self.year = day, month, year

    def __str__(self):
        return "Patcheddatatype(%s, %s, %s)" % (self.day, self.month, self.year)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, obj):
        """ Equality is defined so that we can assert it easier """
        return (self.day == obj.day and
                self.month == obj.month and
                self.year == obj.year)


class TestDaphneCorbaRecoder(object):

    def __init__(self):
        self._on_teardown = []

    def monkey_patch(self, obj, attr, new_value):
        """ Taken from
            http://lackingrhoticity.blogspot.com/2008/12/
            helper-for-monkey-patching-in-tests.html

            Basically it stores the original object before monkeypatching and
            then restores it at teardown. Which is handy, because we do not
            want the object to stay monkeypatched between unit tests (if the
            test needs to do the patch, it can, but it should not change the
            environment for the other tests.
        """
        old_value = getattr(obj, attr)

        def tear_down():
            setattr(obj, attr, old_value)

        self._on_teardown.append(tear_down)
        setattr(obj, attr, new_value)

    def tearDown(self):
        """ Taken from
            http://lackingrhoticity.blogspot.com/2008/12/
            helper-for-monkey-patching-in-tests.html"""
        for func in reversed(self._on_teardown):
            func()

    def setUp(self):
        self.monkey_patch(fredcorba.ccReg, 'DateType', Patched_datetype)

    def test_create(self):
        """ DaphneCorbaRecoder is created with supported encoding. """
        rec = recoder.DaphneCorbaRecode("utf-8")
        assert_is_not_none(rec)

    def test_create_wrong_encoding(self):
        """ DaphneCorbaRecoder raises error for unsupported encoding. """
        assert_raises(recoder.UnsupportedEncodingError,
                      recoder.DaphneCorbaRecode, "invalid coding")

    def test_decode(self):
        """ DaphneCorbaRecoder decodes corba entity to python correctly . """
        rec = recoder.DaphneCorbaRecode("utf-8")
        reg = fredcorba.Registry.Registrar.Detail(
            id=19, ico='', dic='', varSymb='',
            vat=False, handle='NEW REG', name='name 1', organization='',
            street1='', street2='', street3='', city='', stateorprovince='state',
            postalcode='', country='CZ', telephone='', fax='', email='', url='',
            credit='0.00', unspec_credit=u"0.00", access=[], zones=[], hidden=False)
        expected = fredcorba.Registry.Registrar.Detail(
            id=19, ico=u'', dic=u'', varSymb=u'', vat=False,
            handle=u'NEW REG', name=u'name 1', organization=u'', street1=u'',
            street2=u'', street3=u'', city=u'', stateorprovince=u'state',
            postalcode=u'', country=u'CZ', telephone=u'', fax=u'', email=u'',
            url=u'', credit=u'0.00', unspec_credit=u"0.00", access=[], zones=[], hidden=False)

        decoded_reg = rec.decode(reg)
        assert_equal(decoded_reg.__dict__, expected.__dict__)

    def test_encode(self):
        rec = recoder.DaphneCorbaRecode("utf-8")
        python_entity = fredcorba.Registry.Registrar.Detail(
            id=19, ico=u'', dic=u'', varSymb=u'', vat=False,
            handle=u'NEW REG', name=u'name 1', organization=u'', street1=u'',
            street2=u'', street3=u'', city=u'', stateorprovince=u'state',
            postalcode=u'', country=u'CZ', telephone=u'', fax=u'', email=u'',
            url=u'', credit=u'0.00', unspec_credit=u"0.00", access=[],
            zones=[], hidden=False)
        expected = fredcorba.Registry.Registrar.Detail(
            id=19, ico='', dic='', varSymb='',
            vat=False, handle='NEW REG', name='name 1', organization='',
            street1='', street2='', street3='', city='', stateorprovince='state',
            postalcode='', country='CZ', unspec_credit=u"0.00", telephone='',
            fax='', email='', url='', credit='0.00', access=[], zones=[],
            hidden=False)

        encoded_entity = rec.encode(python_entity)

        assert_equal(encoded_entity.__dict__, expected.__dict__)

    def test_encode_date(self):
        rec = recoder.DaphneCorbaRecode("utf-8")
        p_obj = datetime.date(1, 2, 3)
        expected = fredcorba.ccReg.DateType(3, 2, 1)
        res = rec.encode(p_obj)

        assert_equal(res.__dict__, expected.__dict__)

    def test_decode_date_type(self):
        rec = recoder.DaphneCorbaRecode("utf-8")

        d = fredcorba.ccReg.DateType(10, 10, 2009)
        res = rec.decode(d)

        assert_equal(res, datetime.date(2009, 10, 10))

    class Foo():
        """ Fake class for encoding testing. """
        def __init__(self, a, b, c):
            self.a, self.b, self.c = a, b, c

        def __str__(self):

            return "Foo(%s, %s, %s)" % (self.a, self.b, self.c)

        def __repr__(self):
            return self.__str__()

        def __eq__(self, obj):
            """ Equality is defined so that we can assert it easier"""
            return (self.a == obj.a or
                   self.b == obj.b or
                   self.c == obj.c)

    class Bar(Foo):
        """ Fake class for encoding testing. """
        def __str__(self):
            return "Bar(%s, %s, %s)" % (self.a, self.b, self.c)

    def test_encode_double_nested_oldstyle_class(self):
        """ Nested class gets encoded OK.
            Note: We're using old-style classes, because that's what omniORBpy
            does. """
        rec = recoder.DaphneCorbaRecode("utf-8")
        p_ent = TestDaphneCorbaRecoder.Foo(
            1, TestDaphneCorbaRecoder.Bar(
                2, TestDaphneCorbaRecoder.Bar(3, fredtypes.NullDate(), "5"),
                6.0),
            fredtypes.NullInt())
        exp = TestDaphneCorbaRecoder.Foo(
                1, TestDaphneCorbaRecoder.Bar(
                    2, TestDaphneCorbaRecoder.Bar(
                        3, fredcorba.ccReg.DateType(0, 0, 0), "5"), 6.0), 0)
        res = rec.encode(p_ent)

        assert_equal(exp, res)

    def test_encode_nested_date(self):
        rec = recoder.DaphneCorbaRecode("utf-8")

        entity = fredcorba.Registry.Registrar.Detail(
            id=19, ico=u'', dic=u'', varSymb=u'', vat=False,
            handle=u'NEW REG', name=u'name 1', organization=u'', street1=u'',
            street2=u'', street3=u'', city=u'', stateorprovince=u'state',
            postalcode=u'', country=u'CZ', telephone=u'', fax=u'', email=u'',
            url=u'', credit=u'0.00', unspec_credit=u"0.00", access=[],
            zones=[
                fredcorba.ccReg.AdminZoneAccess(
                    id=0, name=u'cz', fromDate=datetime.date(2009, 12, 11),
                    toDate=fredtypes.NullDate())],
            hidden=False)
        expected = fredcorba.Registry.Registrar.Detail(
            id=19, ico='', dic='', varSymb='', vat=False, handle='NEW REG',
            name='name 1', organization='', street1='', street2='',
            street3='', city='', stateorprovince='state',
            postalcode='', country='CZ', telephone='', fax='',
            email='', url='', unspec_credit=u"0.00", credit='0.00', access=[],
            zones=[
                fredcorba.ccReg.AdminZoneAccess(
                    id=0, name='cz', fromDate=fredcorba.ccReg.DateType(
                        day=11, month=12, year=2009),
                    toDate='')],
            hidden=False)
        res = rec.encode(entity)

        assert_equal(expected.__dict__['zones'][0].fromDate,
                     res.__dict__['zones'][0].fromDate)

    def test_sanity(self):
        """ encode(decode(obj)) is equal to obj. """
        rec = recoder.DaphneCorbaRecode("utf-8")
        reg = fredcorba.Registry.Registrar.Detail(
            id=19, ico='', dic='', varSymb='',
            vat=False, handle='NEW REG', name='name 1', organization='',
            street1='', street2='', street3='', city='', stateorprovince='state',
            postalcode='', country='CZ', telephone='', fax='', email='', url='',
            credit='0.00', unspec_credit=u"0.00", access=[], zones=[], hidden=False)

        decoded_reg = rec.decode(reg)
        encoded_reg = rec.encode(decoded_reg)

        assert_equal(encoded_reg.__dict__, reg.__dict__)

    def test_encode_is_idempotent(self):
        # TODO(tom): write the test.
        pass
