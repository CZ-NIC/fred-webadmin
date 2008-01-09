#!/usr/bin/python
# -*- coding: utf-8 -*-

import types

from gpyweb.gpyweb import ul, li


class ErrorDict(dict, ul):
    def __init__(self, from_dict=None, *content, **kwd):
        dict.__init__(self, from_dict or {})
        ul.__init__(self, *content, **kwd)
        self.tag = 'ul'
        self.cssc = 'errors'
        
    def render(self, indent_level = 0):
        self.content = []
        for message in self.values():
            self.add(li(message))
        return super(ErrorDict, self).render(indent_level)

class ErrorList(list, ul):
    def __init__(self, from_list = None, *content, **kwd):
        list.__init__(self, from_list or [])
        ul.__init__(self, *content, **kwd)
        self.tag = 'ul'
        self.cssc = 'errors'
        
    def render(self, indent_level = 0):
        self.content = []
        print 'itemscount:', len(self)
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

    def __deepcopy__(self,memo):
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