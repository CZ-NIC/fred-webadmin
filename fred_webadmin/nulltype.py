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
    __single = None # the one, true Singleton
    
    def __new__(classtype, *args, **kwargs):
        # Check to see if a __single exists already for this class
        # Compare class types instead of just looking for None so
        # that subclasses will create their own __single objects
        if classtype != type(classtype.__single):
            classtype.__single = object.__new__(classtype, *args, **kwargs)
        return classtype.__single

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
    pass


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
