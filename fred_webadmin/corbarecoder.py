import types
import codecs
import exceptions

class UnsupportedEncodingError(Exception):
    pass

class DecodeError(Exception):
    pass

class CorbaRecode(object):
    """ Encodes and decodes corba entities to python entities, i.e.,
        essentially converts corba strings to python strings (type depends on
        specified encoding).
    """ 
    def __init__(self, coding = 'ascii'):
        object.__init__(self)
        self.BasicTypes = (
                types.BooleanType,
                types.FloatType, 
                types.IntType, 
                types.LongType
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

    def decode(self, answer):
        if type(answer) in types.StringTypes:
            return answer.decode(self.coding)
        if type(answer) in self.BasicTypes:
            return answer
        elif type(answer) in self.IterTypes:
            return [ self.decode(x) for x in answer ]
        elif type(answer) == types.InstanceType:
            for name in dir(answer):
                item = getattr(answer, name)
                if name.startswith('__'): 
                    continue # internal python methods / attributes
                if name.startswith('_'): 
                    continue # internal module defined methods / attributes
                if type(item) == types.MethodType: 
                    continue # methods - don't call them
                if type(item) in self.BasicTypes:
                    continue # nothing to do
                if type(item) in types.StringTypes:
                    answer.__dict__[name] = item.decode(self.coding)
                    continue
                if type(item) == types.InstanceType:
                    answer.__dict__[name] = self.decode(item)
                    continue
                if type(item) in self.IterTypes:
                    answer.__dict__[name] = [ self.decode(x) for x in item ]
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
            return [ self.encode(x) for x in answer ]
        elif type(answer) == types.InstanceType:
            for name in dir(answer):
                item = getattr(answer, name)
                if name.startswith('__'): 
                    continue # internal python methods / attributes
                if name.startswith('_'): 
                    continue # internal module defined methods / attributes
                if type(item) == types.MethodType: 
                    continue # methods - don't call them
                if type(item) in self.BasicTypes:
                    continue # nothing to do
                if type(item) in types.StringTypes:
                    answer.__dict__[name] = item.encode(self.coding)
                    continue
                if type(item) == types.InstanceType:
                    answer.__dict__[name] = self.encode(item)
                    continue
                if type(item) in self.IterTypes:
                    answer.__dict__[name] = [ self.encode(x) for x in item ]
                    continue
                raise ValueError(
                    "%s attribute in %s is not convertable to python type." % (
                        name, answer))
            return answer
