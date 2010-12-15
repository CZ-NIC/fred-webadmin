#
# Achoo. A fluent interface for testing Python objects.
# Copyright (C) 2008 Quuxo Software.
# <http://web.quuxo.com/projects/achoo>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#

"""
Achoo is a fluent interface for testing Python objects.

It is designed to be used in conjunction with a unit testing
framework like PyUnit's C{unittest} module, shipped with all modern
Python distributions.

To use Achoo, import the assertion builder functions then use them
to wire up assertions about objects and callables.

The two assertion builder functions are C{requiring} - used to test
properties of objects and C{calling}, used to test properties of a
calling a callable object (that is, a function, method or similar).
These functions returns assertion builders that can be used to chain
assertions calls together. See the documentation for the functions
for more information.

If any of the assertions are not met, an C{AssertionError} is raised.

For example::

    import unittest
    from achoo import requiring
    from achoo import calling

    class StringTest(unittest.TestCase):

        def testLength(self):
            s = 'foo'
            requiring(s.length).equal_to(3)

        def testStrip(self):
            s = ' foo '
            calling(s.strip).returns('foo')

        def testSplit(self):
            s = 'foo,bar'
            calling(s.split).passing(',').returns()\ 
                .length(2)\ 
                .index(0).equal_to('foo')\ 
                .index(1).equal_to('bar')

        def testBadIndex(self):
            s = 'foo'
            calling(s.index).passing('quux').raises(ValueError)

"""

import sys

import gettext
_ = gettext.translation('achoo', fallback=True).ugettext


def requiring(value):
    """
    Assertion builder factory for object properties.

    To test an object, call C{requiring} and pass the object as the
    sole argument. A C{ValueAssertionBuilder} is returned and can be used
    to chain together assertions about it.

    For example::

        test_map = {'foo': 'bar'}
        requiring(test_map)\
            .length(1)\
            .contains('foo')\
            .index('foo').equal_to('bar')

    @return: an instance of C{ValueAssertionBuilder} wrapping the value
    passed in
    @param value: an object to be tested
    """
    # XXX maybe put some logging here? what about lookup
    # for different builder types depending on the given type?
    # otherwise this could probably be an alias for the builder
    # constructor
    return ValueAssertionBuilder(value)


class ValueAssertionBuilder(object):
    """
    An assertion builder for testing properties of objects.

    This object can be used to create a set of assertions about various
    properties of an object. Most methods return a builder with the
    same object so that more than one assertion to be made about it.

    If any of the assertions fail, an C{AssertionError} is raised.
    """

    def __init__(self, value, invert=False):
        """
        Constructs a new builder.

        In general, you want to use the C{requiring} function instead
        of this directly.

        @param value: an object to be tested
        @param invert: optionally inverts the sense of the next assertion
        if C{True}
        """
        self.value = value
        self.invert_sense = invert


    @property
    def is_not(self):
        """
        Inverts the sense of the next assertion.

        This property causes the boolean sense of the next assertion
        to be inverted. That is, if a call to C{equal_to} is prefixed
        with C{is_not}, it will raise an error if the value object is
        not equal to the given value. All other subsequent assertions
        retain the specified sense unless also prefixed with C{is_not}.

        For example::

            s = 'foo'
            requiring(s.length).is_not.equal_to(0)

        """
        return ValueAssertionBuilder(self.value, True)


    def equal_to(self, other):
        """
        Asserts the value object is equal to some other object.

        @return: this assertion builder
        @param other: another object to test against the builder's
        value object
        @raise AssertionError: if the builder's value is not equal to
        C{other}
        """
        if self.value != other and not self.invert_sense:
            raise self._error(_('Value `%s\' expected to equal `%s\''),
                              _('Value `%s\' not expected to equal `%s\''),
                              other)
        self.invert_sense = False
        return self


    def same_as(self, other):
        """
        Asserts the value object is the same as another object.

        @return: this assertion builder
        @param other: another object to test for same identity
        @raise AssertionError: if the builder's value is not the same
        object as C{other}
        """
        if self.value is not other and not self.invert_sense:
            raise self._error(_('Value `%s\' expected to be `%s\''),
                              _('Value `%s\' not expected to be `%s\''),
                              other)
        self.invert_sense = False
        return self


    def is_none(self):
        """
        Asserts the value object is C{None}.

        @return: this assertion builder
        @raise AssertionError: if the builder's value is not C{None}
        """
        return self.same_as(None)


    def is_not_none(self):
        """
        Asserts the value object is not C{None}.

        @return: this assertion builder
        @raise AssertionError: if the builder's value is C{None}
        """
        if self.value is None and not self.invert_sense:
            raise self._error(_('Value `%s\' expected to be `%s\''),
                              _('Value `%s\' not expected to be `%s\''),
                              None)
        self.invert_sense = False
        return self


    def is_a(self, clazz):
        """
        Asserts the value object is an instance of a particular type.

        @return: this assertion builder
        @param clazz: type the value must be an instance of
        @raise AssertionError: if the builder's value is not an instance
        of C{clazz}
        """
        if not isinstance(self.value, clazz) and not self.invert_sense:
            raise self._error(_('Value `%s\' expected to be a `%s\''),
                              _('Value `%s\' not expected to be a `%s\''),
                              clazz)
        self.invert_sense = False
        return self


    def length(self, length):
        """
        Asserts the value object has a specific length.

        @return: this assertion builder
        @param length: the value that must be returned by passing
        the builder value to the C{len} built-in
        @raise AssertionError: if the length of the builder's value is
        not equal to C{length}
        """
        if len(self.value) != length and not self.invert_sense:
            raise self._error(_('Length of `%s\' expected to equal `%s\''),
                              _('Length of `%s\' not expected to equal `%s\''),
                              length)
        self.invert_sense = False
        return self


    def contains(self, element):
        """
        Asserts the value object contains a specific element.

        @return: this assertion builder
        @param element: the element that must be contained by the
        value object, as tested using the keyword C{in}
        @raise AssertionError: if the builder's value does not contain
        C{element}
        """
        if element not in self.value and not self.invert_sense:
            raise self._error(_('Value `%s\' expected to contain `%s\''),
                              _('Value of `%s\' not expected to contain `%s\''),
                              element)
        self.invert_sense = False
        return self


    def index(self, index):
        """
        Asserts the value object has a specific index.

        B{Note:} this method returns a builder for the object at the
        given index, allowing assertions to be made about that object
        but not allowing any additional assertions to be made about
        the original object.

        The C{is_not} modifier has no effect on this method.

        For example::

            test_map = {'foo': 'bar'}
            requiring(test_map).index('foo').equal_to('bar')

        @return: an assertion builder for the object at the given
        index
        @param index: the index that must be contained by the
        value object, as tested using the keyword C{in}
        @raise AssertionError: if the builder's value does not contain
        an element at C{index}
        """
        if self.invert_sense:
            raise AssertionError\
                (_('A call to `index\' cannot be preceded by `is_not\''))

        try:
            return ValueAssertionBuilder(self.value[index])
        except KeyError:
            raise self._error(_('Value `%s\' expected to contain key `%s\''),
                              None, index)
        except IndexError:
            raise self._error(_('Value `%s\' expected to contain index `%s\''),
                              None, index)

    def _error(self, message, inverse_message, other):
        """
        Returns a new C{AssertionError} with an appropriate message.
        """
        return AssertionError((message
                               if not self.invert_sense
                               else inverse_message) % (self.value, other))


def calling(callabl):
    """
    Assertion builder factory for callable objects.

    To test a callable, call C{requiring} and pass the object as the
    sole argument. A C{ValueAssertionBuilder} is returned and can be used
    to chain together assertions about it.

    For example::

        incr = lambda x: x + 1
        calling(incr).passing(1).returns(2)
        calling(incr).raises(TypeError)

    @return: an instance of C{CallableAssertionBuilder} wrapping the
    callable passed in
    @param callabl: a callable object (function, method or similar) to
    be tested
    """
    # XXX maybe put some logging here? what about lookup
    # for different builder types depending on the given type?
    # otherwise this could probably be an alias for the builder
    # constructor
    return CallableAssertionBuilder(callabl)


class CallableAssertionBuilder(object):
    """
    An assertion builder for testing callable objects.

    This object can be used to create a set of assertions about
    conditions when calling a callable object, such as a function
    or method.

    To provide parameters to the callable, use the C{passing} method.
    The callable is not actually executed until one of the return
    or raises methods is called.
    """

    def __init__(self, callabl):
        """
        Constructs a new builder.

        In general, you want to use the C{calling} function instead
        of this directly.

        @param callabl: an object to be tested
        """
        self.callable = callabl
        self.args = None
        self.kwargs = None

    def passing(self, *args, **kwargs):
        """
        Applies a set of arguments to be passed to the callable.

        Use this method to specify what positional and keyword arguments
        should be passed to the callable.

        @return: this assertion builder
        @param args: positional arguments to be passed to the callable
        @param kwargs: keyword arguments to be passed to the callable
        """
        self.args = args
        self.kwargs = kwargs
        return self

    def returns(self, value=None):
        """
        Invokes the callable, optionally checking the returned value.

        Calling this method will cause the callable to be invoked,
        with any arguments specified using C{passing} and returning
        a C{ValueAssertionBuilder} for the object returned by the
        callable.

        An object can be optionally passed to this method for
        conveniently checking the value of the object returned
        by the callable.

        @return: a C{ValueAssertionBuilder} for the object returned
        by the invocation of the callable
        @param value: optional value that must be equal to the
        object returned by invoking the callable
        @raise AssertionError: if the returned value is not equal to
        C{value}
        """
        ret = self._invoke()
        builder = requiring(ret)
        if value is not None:
            builder.equal_to(value)
        return builder

    def returns_none(self):
        """
        Invokes the callable and ensures the return value is C{None}.

        Calling this method will cause the callable to be invoked,
        with any arguments specified using C{passing}.

        @raise AssertionError: if the value returned by invoking
        the callable is not equal to C{None}
        """
        self.returns().is_none()

    def raises(self, error):
        """
        Invokes the callable, ensuring it raises an exception.

        Calling this method will cause the callable to be invoked,
        with any arguments specified using C{passing}.

        A C{ValueAssertionBuilder} for the exception is returned,
        allowing its properties to be examined.

        @return: a C{ValueAssertionBuilder} for the exception raised
        by the invocation of the callable
        @param error: type of the exception to be raised
        @raise AssertionError: if the callable invocation did not
        raise an exception or if it raised an exception that was
        not of type C{BaseException}
        """
        try:
            self._invoke()
        except:
            e_type, e_value, tb = sys.exc_info()
            if e_type == error:
                return requiring(e_value)

            raise AssertionError(_('Calling `%s\' raised a `%s\' error')
                                 % (self.callable, e_type))
        else:
            raise AssertionError(_('Calling `%s\' did not raise any error')
                                 % self.callable)

    def _invoke(self):
        """
        Invokes the callable with any parameters that have been specified.

        @return: the return value from the callable invocation
        """
        if self.args and self.kwargs:
            return self.callable(*self.args, **self.kwargs)
        if self.args:
            return self.callable(*self.args)
        if self.kwargs:
            return self.callable(**self.kwargs)
        return self.callable()

