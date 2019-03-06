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

""" Null object - or rather it's subclasses - is used in Daphne to explicitly
    state that a given field (with a certain type - that's when subclassing
    Null jumps in) is blank when the form is submitted.

    Using None does not suffice as we need to be able to convert the blakn
    field value to the appropriate corba type before sending it to the server.
"""


class Singleton(object):
    """ Singleton pattern (only one instance is created).

        Doctest:
            >>> a = Singleton()
            >>> b = Singleton()
            >>> a is b
            True
    """
    __single = None  # the one, true Singleton

    def __new__(cls, *args, **kwargs):
        # Check to see if a __single exists already for this class
        # Compare class types instead of just looking for None so
        # that subclasses will create their own __single objects
        if cls != type(cls.__single):
            cls.__single = object.__new__(cls, *args, **kwargs)
        return cls.__single

    def __init__(self, name=None):
        self.name = name


class Null(Singleton):
    """ Object representing null value.
        In Daphne primarily used for subclassing and the subclasses used for
        blank form field values (so that we can preserve the type information).

        Doctest:
            >>> a = Null()
            >>> b = Null()
            >>> a is b
            True
    """
    def __nonzero__(self):
        return False

    def __eq__(self, obj):
        return isinstance(obj, Null)

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def __cmp__(self, obj):
        if self.__eq__(obj):
            return 0
        else:
            return -1

    def __str__(self):
        return 'None'


class NullDate(Null):
    pass


class NullDateTime(Null):
    pass


class NullInt(Null):
    pass


class NullFloat(Null):
    pass


class NullDecimal(Null):
    pass


class NullFile(Null):
    pass


class NullImage(Null):
    pass
