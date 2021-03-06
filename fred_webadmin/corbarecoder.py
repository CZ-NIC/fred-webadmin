#
# Copyright (C) 2008-2018  CZ.NIC, z. s. p. o.
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

import types
import codecs
import datetime

from pyfco.recoder import decode_iso_date, decode_iso_datetime, encode_iso_date, encode_iso_datetime

import fred_webadmin.nulltype as fredtypes
from corba import ccReg, Registry


class UnsupportedEncodingError(Exception):
    pass


class DecodeError(Exception):
    pass


class CorbaRecode(object):
    """ Encodes and decodes corba entities to python entities, i.e.,
        essentially converts corba strings to python strings (type depends on
        specified encoding).
    """
    def __init__(self, coding='ascii'):
        object.__init__(self)
        self.BasicTypes = (
                types.BooleanType,
                types.FloatType,
                types.IntType,
                types.LongType,
                types.NoneType
                )
        self.IterTypes = (
                types.TupleType,
                types.ListType
                )
        try:
            codecs.lookup(coding)
            self.coding = coding
        except LookupError, e:
            raise UnsupportedEncodingError(e)

    def isInstance(self, obj):
        return type(obj) == types.InstanceType or (hasattr(obj, '__class__') and ('__dict__' in dir(obj) or hasattr(obj, '__slots__')))

    def decode(self, answer):
        if type(answer) in types.StringTypes:
            return answer.decode(self.coding)
        if type(answer) in self.BasicTypes:
            return answer
        elif type(answer) in self.IterTypes:
            return [self.decode(x) for x in answer]
        elif self.isInstance(answer):
            for name in dir(answer):
                item = getattr(answer, name)
                if name.startswith('__'):
                    continue  # internal python methods / attributes
                if name.startswith('_'):
                    continue  # internal module defined methods / attributes
                if type(item) == types.MethodType:
                    continue  # methods - don't call them
                if type(item) in self.BasicTypes:
                    continue  # nothing to do
                if type(item) in types.StringTypes:
                    answer.__dict__[name] = item.decode(self.coding)
                    continue
                if self.isInstance(item):
                    answer.__dict__[name] = self.decode(item)
                    continue
                if type(item) in self.IterTypes:
                    answer.__dict__[name] = [self.decode(x) for x in item]
                    continue
                raise ValueError(
                    "%s attribute in %s is not convertable to CORBA." % (
                        name, answer))
            return answer

    def encode(self, answer):
        if type(answer) in types.StringTypes:
            return answer.encode(self.coding)
        if type(answer) in self.BasicTypes:
            return answer
        elif type(answer) in self.IterTypes:
            return [self.encode(x) for x in answer]
        elif self.isInstance(answer):
            for name in dir(answer):
                item = getattr(answer, name)
                if name.startswith('__'):
                    continue  # internal python methods / attributes
                if name.startswith('_'):
                    continue  # internal module defined methods / attributes
                if type(item) == types.MethodType:
                    continue  # methods - don't call them
                if type(item) in self.BasicTypes:
                    continue  # nothing to do
                if type(item) in types.StringTypes:
                    answer.__dict__[name] = item.encode(self.coding)
                    continue
                if self.isInstance(item):
                    answer.__dict__[name] = self.encode(item)
                    continue
                if type(item) in self.IterTypes:
                    answer.__dict__[name] = [self.encode(x) for x in item]
                    continue
                raise ValueError(
                    "%s attribute in %s is not convertable to python type." % (
                        name, answer))
            return answer


class DaphneCorbaRecode(CorbaRecode):
    """ TODO(tom): Bad code duplication here, refactor mercilessly!
        Used to encode python objects to corba objects and decode corba objects
        to python objects.
    """
    def decode(self, answer):
        if type(answer) in types.StringTypes:
            return answer.decode(self.coding)
        if type(answer) in self.BasicTypes:
            return answer
        elif type(answer) in self.IterTypes:
            return [self.decode(x) for x in answer]
        if isinstance(answer, ccReg.DateTimeType):
            return corba_to_datetime(answer)
        if isinstance(answer, ccReg.DateType):
            return corba_to_date(answer)
        if isinstance(answer, ccReg.DateType):
            return corba_to_date(answer)
        if isinstance(answer, Registry.IsoDate):
            return decode_iso_date(answer)
        if isinstance(answer, Registry.IsoDateTime):
            return decode_iso_datetime(answer)
        # OMNIOrbpy uses old style classes => check whether type is
        # InstanceType.
        if self.isInstance(answer):
            for name in dir(answer):
                item = getattr(answer, name)
                if name.startswith('_') and name != "_from":
                    # HACK to handle that OMNIOrb mangles 'from' to '_from'
                    continue  # internal module defined methods / attributes
                if isinstance(item, (types.MethodType,) + self.BasicTypes):
                    continue  # None or methods - don't call them
                if type(item) in types.StringTypes:
                    answer.__dict__[name] = item.decode(self.coding)
                    continue
                if self.isInstance(item):
                    answer.__dict__[name] = self.decode(item)
                    continue
                if type(item) in self.IterTypes:
                    answer.__dict__[name] = [self.decode(x) for x in item]
                    continue
                raise ValueError(
                    "%s attribute in %s is not convertable to python type." % (
                        name, answer))
            return answer

    def encode(self, answer):
        if type(answer) in types.StringTypes:
            return answer.encode(self.coding)
        if type(answer) in self.BasicTypes:
            return answer
        elif type(answer) in self.IterTypes:
            return [self.encode(x) for x in answer]
        if isinstance(answer, datetime.datetime):
            return datetime_to_corba(answer)
        if isinstance(answer, datetime.date):
            return date_to_corba(answer)
        # encode function ignored special valuetypes. Those are now
        # included in isInstance checking, so they have to be
        # ignored specially
        suc, val = _encode_null_type(answer, None)
        if suc:
            return
        # OMNIOrbpy uses old style classes => check whether type is
        # InstanceType.
        if self.isInstance(answer):
            for name in dir(answer):
                item = getattr(answer, name)
                if name.startswith('__'):
                    continue  # internal python methods / attributes
                if name.startswith('_'):
                    continue  # internal module defined methods / attributes
                if type(item) == types.MethodType:
                    continue  # methods - don't call them
                if type(item) in self.BasicTypes:
                    continue  # nothing to do
                if type(item) in types.StringTypes:
                    answer.__dict__[name] = item.encode(self.coding)
                    continue
                suc, val = _encode_null_type(item, answer)
                if suc:
                    answer.__dict__[name] = val
                    continue
                if self.isInstance(item):
                    answer.__dict__[name] = self.encode(item)
                    continue
                if type(item) in self.IterTypes:
                    answer.__dict__[name] = [self.encode(x) for x in item]
                    continue
                if type(item) == datetime.date or \
                  type(item) == datetime.datetime:
                    answer.__dict__[name] = self.encode(item)
                    continue
                raise ValueError(
                    "%s attribute in %s is not convertable to Corba type." % (
                        name, answer))
            return answer


class IsoDateTimeCorbaRecode(DaphneCorbaRecode):
    """Corba recoder for IsoDate and IsoDateTime format support."""

    def encode(self, answer):
        from fred_webadmin.utils import get_local_timezone

        if isinstance(answer, datetime.datetime):
            if answer.tzinfo is None:
                answer = get_local_timezone().localize(answer)
            return encode_iso_datetime(answer)
        if isinstance(answer, datetime.date):
            return encode_iso_date(answer)
        return super(IsoDateTimeCorbaRecode, self).encode(answer)


null_encoding_rules = {
    fredtypes.NullDate: ccReg.DateType(0, 0, 0),
    fredtypes.NullDateTime: ccReg.DateTimeType(0, 0, 0, 0),
    fredtypes.NullInt: 0,
    fredtypes.NullDecimal: 0,
    fredtypes.NullFloat: 0.0,
}


def _encode_null_type(item, objref):
    """ Transforms the Null subclass object to the respective CORBA type.
    """
    if type(item) in null_encoding_rules:
        return (True, null_encoding_rules[type(item)])
    if isinstance(item, fredtypes.Null):
        return (True, "")
    return (False, None)


recoder = DaphneCorbaRecode('utf-8')
c2u = recoder.decode  # recode from corba string to unicode
u2c = recoder.encode  # recode from unicode to strings


def date_to_corba(date):
    """ onverted to ccReg.DateType. If date is None, then
        ccReg.DateType(0, 0, 0) is returned.

        Arguments:
            date:
                datetime.date() or fredtypes.NullDate.
    """
    return date and ccReg.DateType(*reversed(date.timetuple()[:3])) or ccReg.DateType(0, 0, 0)


def corba_to_date(corba_date):
    if corba_date.year == 0:  # empty date is in corba = DateType(0, 0, 0)
        return fredtypes.NullDate()
    return datetime.date(corba_date.year, corba_date.month, corba_date.day)


def datetime_to_corba(date_time):
    if date_time:
        t_tuple = date_time.timetuple()
        return ccReg.DateTimeType(ccReg.DateType(*reversed(t_tuple[:3])), *t_tuple[3:6])
    else:
        return ccReg.DateTimeType(ccReg.DateType(0, 0, 0), 0, 0, 0)


def corba_to_datetime(corba_date_time):
    corba_date = corba_date_time.date
    if corba_date.year == 0:  # empty date is in corba = DateType(0, 0, 0)
        return fredtypes.NullDateTime()
    return datetime.datetime(corba_date.year, corba_date.month, corba_date.day,
                             corba_date_time.hour, corba_date_time.minute, corba_date_time.second)


def date_time_interval_to_corba(val, date_conversion_method):
    '''
    val is list, where first three values are ccReg.DateType or ccReg.DateTimeType, according to that,
    it should be called with date_coversion_method date_to_corba or date_time_interval_to_corba,
    next in list is offset and ccReg.DateTimeIntervalType
    '''
    if date_conversion_method == date_to_corba:
        interval_type = ccReg.DateInterval
    else:
        interval_type = ccReg.DateTimeInterval
    c_from, c_to, c_day = [date_conversion_method(date) for date in val[:3]]
    if int(val[3]) == ccReg.DAY._v:
        corba_interval = interval_type(c_day, c_to, ccReg.DAY, val[4] or 0)  # c_to will be ignored
    else:
        corba_interval = interval_type(c_from, c_to, ccReg.DateTimeIntervalType._items[val[3]], val[4] or 0)
    return corba_interval


def corba_to_date_time_interval(val, date_conversion_method):
    if val.type == ccReg.DAY:
        return [None, None, date_conversion_method(val._from), val.type._v, 0]
    elif val.type == ccReg.INTERVAL:
        return [date_conversion_method(val._from), date_conversion_method(val.to), None, val.type._v, 0]
    else:
        return [None, None, None, val.type._v, val.offset]
