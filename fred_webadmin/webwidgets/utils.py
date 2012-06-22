#!/usr/bin/python
# -*- coding: utf-8 -*-

import types
import copy
from copy import deepcopy
from gpyweb.gpyweb import ul, li


class ErrorDict(dict, ul):
    def __init__(self, from_dict=None, *content, **kwd):
        dict.__init__(self, from_dict or {})
        ul.__init__(self, *content, **kwd)
        self.tag = 'ul'
        self.cssc = 'errorlist'

    def render(self, indent_level=0):
        self.content = []
        for message in self.values():
            self.add(li(message))
        return super(ErrorDict, self).render(indent_level)

class ErrorList(list, ul):
    def __init__(self, from_list=None, *content, **kwd):
        list.__init__(self, from_list or [])
        ul.__init__(self, *content, **kwd)
        self.tag = 'ul'
        self.cssc = 'errorlist'

    def render(self, indent_level=0):
        self.content = []
        for message in self:
            self.add(li(message))
        return super(ErrorList, self).render(indent_level)

class ValidationError(Exception):
    def __init__(self, message):
        "ValidationError can be passed a string or a list."
        if isinstance(message, list):
            self.messages = ErrorList(message)
        else:
            assert isinstance(message, basestring), ("%s should be a basestring" % repr(message))
            self.messages = ErrorList([message])

    def __str__(self):
        # This is needed because, without a __str__(), printing an exception
        # instance would result in this:
        # AttributeError: ValidationError instance has no attribute 'args'
        # See http://www.python.org/doc/current/tut/node10.html#handling
        return repr(self.messages)


class SortedDict(dict):
    """
    A dictionary that keeps its keys in the order in which they're inserted.
    """
    def __init__(self, data=None):
        if data is None:
            data = {}
        dict.__init__(self, data)
        if isinstance(data, dict):
            self.keyOrder = data.keys()
        else:
            self.keyOrder = [key for key, value in data]

    def __deepcopy__(self, memo):
        from copy import deepcopy
        obj = self.__class__()
        for k, v in self.items():
            obj[k] = deepcopy(v, memo)
        return obj

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        if key not in self.keyOrder:
            self.keyOrder.append(key)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self.keyOrder.remove(key)

    def __iter__(self):
        for k in self.keyOrder:
            yield k

    def pop(self, k, *args):
        result = dict.pop(self, k, *args)
        try:
            self.keyOrder.remove(k)
        except ValueError:
            # Key wasn't in the dictionary in the first place. No problem.
            pass
        return result

    def popitem(self):
        result = dict.popitem(self)
        self.keyOrder.remove(result[0])
        return result

    def items(self):
        return zip(self.keyOrder, self.values())

    def iteritems(self):
        for key in self.keyOrder:
            yield key, dict.__getitem__(self, key)

    def keys(self):
        return self.keyOrder[:]

    def iterkeys(self):
        return iter(self.keyOrder)

    def values(self):
        return [dict.__getitem__(self, k) for k in self.keyOrder]

    def itervalues(self):
        for key in self.keyOrder:
            yield dict.__getitem__(self, key)

    def update(self, dict):
        for k, v in dict.items():
            self.__setitem__(k, v)

    def setdefault(self, key, default):
        if key not in self.keyOrder:
            self.keyOrder.append(key)
        return dict.setdefault(self, key, default)

    def value_for_index(self, index):
        """Returns the value of the item at the given zero-based index."""
        return self[self.keyOrder[index]]

    def insert(self, index, key, value):
        """Inserts the key, value pair before the item with the given index."""
        if key in self.keyOrder:
            n = self.keyOrder.index(key)
            del self.keyOrder[n]
            if n < index:
                index -= 1
        self.keyOrder.insert(index, key)
        dict.__setitem__(self, key, value)

    def copy(self):
        """Returns a copy of this object."""
        # This way of initializing the copy means it works for subclasses, too.
        obj = self.__class__(self)
        obj.keyOrder = self.keyOrder
        return obj

    def deepcopy(self):
        return SortedDict([(k, deepcopy(v)) for k, v in self.items()])

    def __repr__(self):
        """
        Replaces the normal dict.__repr__ with a version that returns the keys
        in their sorted order.
        """
        return '{%s}' % ', '.join(['%r: %r' % (k, v) for k, v in self.items()])

def pretty_name(name):
    "Converts 'first_name' to 'First name'"
    name = name[0].upper() + name[1:]
    return name.replace('_', ' ')

def isiterable(par):
    # we don't want to iterate over string characters
    if isinstance(par, types.StringTypes):
        return False
    try:
        iter(par)
        return True
    except TypeError:
        return False

def escape_js_literal(literal):
    return literal.replace('\n', '\\n\\\n').replace("'", "\\'").replace('<', '\\<').replace('>', '\\>')


def convert_linear_filter_to_form_output(or_filters):
    ''' Get filters in linear form (see FilterPanel) and converts it to
        the same output as FilterForm (see UnionFilterForm and FilterForm)
    '''
    def create_or_get_filter(new_or_filter, fname):
        splitted_name = fname.split('.')
        tmp_filter = new_or_filter
        for name in splitted_name[:-1]: # last is actual name of filter
            if not tmp_filter.has_key(name):
                tmp_filter['presention|' + name] = 'on'
                tmp_filter[name] = {}
            tmp_filter = tmp_filter[name]
        return tmp_filter, splitted_name[-1]

    def create_or_get_filter_multifield(new_or_filter, filter_name):
        out_filter = new_or_filter
        out_filter["presention|%s" % filter_name] = 'on'
        return out_filter, filter_name

    result = []
    for or_filter in or_filters:
        new_or_filter = {}
        for fname, fval in or_filter.items():
            if isinstance(fval, dict):
                current_filter, last_fname = create_or_get_filter_multifield(new_or_filter, fname)
            else:
                current_filter, last_fname = create_or_get_filter(new_or_filter, fname)

            # negation is expressed by fval==[True, fval] instead on just fval,
            # here could be problem, if some field could return list of
            # 2 booleans or so, but it is unlikely, and we get much cleaner
            # notation of filter (as negation is rarely used)
            if isinstance(fval, (types.ListType, types.TupleType)) and \
               len(fval) == 2 and isinstance(fval[0], types.BooleanType):
                negation = True
                fval = fval[1]
            else:
                negation = False

            # TODO(tom): REFACTOR!
            if not isinstance(fval, dict):
                current_filter['presention|' + last_fname] = 'on'
                current_filter[last_fname] = fval
            else:
                current_filter['presention|' + last_fname] = 'on'
                current_filter.update(fval)
            if negation:
                current_filter['negation|' + last_fname] = 'on'
        result.append(new_or_filter)
    return result

def find_and_update_datetime_offset_in_json(json_data, delta):
    """
        >>> json_data = {u'SvTRID': u'', u'presention|SvTRID': u'000', u'presention|Time': u'on', u'Time/4': u'0', u'Time/1/1/0': u'0', u'Time/0/0': u'', u'Time/2': u'', u'Time/3': u'12', u'Time/0/1/1': u'0', u'Time/0/1/0': u'0', u'Time/1/0': u'', u'Time/1/1/1': u'0'}
        >>> res = find_and_update_datetime_offset_in_json(json_data, 1)
        >>> expected = {u'SvTRID': u'', u'presention|SvTRID': u'000', u'presention|Time': u'on', u'Time/4': u'1', u'Time/1/1/0': u'0', u'Time/0/0': u'', u'Time/2': u'', u'Time/3': u'12', u'Time/0/1/1': u'0', u'Time/0/1/0': u'0', u'Time/1/0': u'', u'Time/1/1/1': u'0'}
        >>> res == expected
        True

        >>> json_data = {u'SvTRID': u'', u'presention|SvTRID': u'000', u'presention|Time': u'on', u'Time/4': u'0', u'Time/1/1/0': u'0', u'Time/0/0': u'', u'Time/2': u'', u'Time/3': u'12', u'Time/0/1/1': u'0', u'Time/0/1/0': u'0', u'Time/1/0': u'', u'Time/1/1/1': u'0'}
        >>> res = find_and_update_datetime_offset_in_json(json_data, -1)
        >>> expected = {u'SvTRID': u'', u'presention|SvTRID': u'000', u'presention|Time': u'on', u'Time/4': u'-1', u'Time/1/1/0': u'0', u'Time/0/0': u'', u'Time/2': u'', u'Time/3': u'12', u'Time/0/1/1': u'0', u'Time/0/1/0': u'0', u'Time/1/0': u'', u'Time/1/1/1': u'0'}
        >>> res == expected
        True

        >>> json_data = [{"list_not_a_dict": "invalid"}]
        >>> res = find_and_update_datetime_offset_in_json(json_data, 1)
        Traceback (most recent call last):
        ...
        ValueError: The parameter must be a dict!
    """
    if not isinstance(json_data, dict):
        raise ValueError("The parameter must be a dict!")
    # Copying is not necessary, but we do it anyway.
    json_data = copy.copy(json_data)
    offset = json_data.get('Time/4')
    offset = int(offset)
    offset = offset + delta
    json_data['Time/4'] = unicode(offset)
    return json_data

def convert_corba_obj_to_form_data(corba_obj):
    data = corba_obj.__dict__
    for key in dict:
        val = dict[key]
        if isinstance(val, [types.StringTypes, types.BooleanType]):
            pass
        elif isinstance(val, [types.IntType, types.FloatType]):
            dict[key] = unicode(val)
        elif isinstance(val, [types.TupleType, types.ListType]):
            inner_data = []
            for inner_corba_obj in val:
                inner_data.append(convert_corba_obj_to_form_data(inner_corba_obj))
            dict[key] = unicode(val)
        else:
            raise RuntimeError('Unknown corba type, unable to convert it to form data')

    return data
