import types
import codecs
import exceptions

class UnsupportedEncodingError(Exception):
    pass

class DecodeError(Exception):
    pass

class CorbaRecode(object):

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
        except (codecs.LookupError,), (val, no):
            raise UnsupportedEncodingError(val, no)

    def decode(self, answer):
        if type(answer) in types.StringTypes:
#            try:
#                answer.decode('ascii')
#                return answer
#            except UnicodeDecodeError:
            return answer.decode(self.coding)
        if type(answer) in self.BasicTypes:
            return answer
        elif type(answer) in self.IterTypes:
            return [ self.decode(x) for x in answer ]
        elif type(answer) == types.InstanceType:
            # EXTRA: types which needs extra treating should be evaluated first
            # special case - "CORBA.EnumItem" type
            # probably omniORB specific ('EnumItem' can be implemented as type, not only as class)
#            if answer.__class__.__name__ == 'EnumItem':
#                return self.decode(answer._n)
            # EXTRA: end
            for name in dir(answer):
                item = getattr(answer, name)
                # EXTRA: types which needs extra treating should be evaluated first
                # special case - "CORBA.Any" type
                # probably omniORB specific ('Any' can be implemented as type, not only as class)
#                if answer.__class__.__name__ == 'Any' and (name == 'value') and (type(item) == types.MethodType):
#                    return self.decode(item())
                # EXTRA: end
                if name.startswith('__'): continue # internal python methods / attributes
                if type(item) in types.StringTypes:
#                    try:
#                        item.decode('ascii')
#                        answer.__dict__[name] = item
#                    except UnicodeDecodeError:
                    #print "III:", item, type(item), repr(item)
                    answer.__dict__[name] = item.decode(self.coding)
                if name.startswith('_'): continue # internal module defined methods / attributes
                if type(item) == types.MethodType: continue # methods - don't call them
                if type(item) == types.InstanceType:
                    answer.__dict__[name] = self.decode(item)
                if type(item) in self.IterTypes:
                    answer.__dict__[name] = [ self.decode(x) for x in item ]
            return answer
        
    def encode(self, answer):
        if type(answer) in types.StringTypes:
#            try:
#                answer.encode('ascii')
#                return answer
#            except UnicodeencodeError:
            return answer.encode(self.coding)
        if type(answer) in self.BasicTypes:
            return answer
        elif type(answer) in self.IterTypes:
            return [ self.encode(x) for x in answer ]
        elif type(answer) == types.InstanceType:
            # EXTRA: types which needs extra treating should be evaluated first
            # special case - "CORBA.EnumItem" type
            # probably omniORB specific ('EnumItem' can be implemented as type, not only as class)
#            if answer.__class__.__name__ == 'EnumItem':
#                return self.encode(answer._n)
            # EXTRA: end
            for name in dir(answer):
                item = getattr(answer, name)
                # EXTRA: types which needs extra treating should be evaluated first
                # special case - "CORBA.Any" type
                # probably omniORB specific ('Any' can be implemented as type, not only as class)
#                if answer.__class__.__name__ == 'Any' and (name == 'value') and (type(item) == types.MethodType):
#                    return self.encode(item())
                # EXTRA: end
                if name.startswith('__'): continue # internal python methods / attributes
                if type(item) in types.StringTypes:
#                    try:
#                        item.encode('ascii')
#                        answer.__dict__[name] = item
#                    except UnicodeencodeError:
                    answer.__dict__[name] = item.encode(self.coding)
                if name.startswith('_'): continue # internal module defined methods / attributes
                if type(item) == types.MethodType: continue # methods - don't call them
                if type(item) == types.InstanceType:
                    answer.__dict__[name] = self.encode(item)
                if type(item) in self.IterTypes:
                    answer.__dict__[name] = [ self.encode(x) for x in item ]
            return answer

#    def decode_to_dict(self, corba_obj):
#        ''' Takes corba object and return dict created from it, its values are recursively
#            decoded to dict, too.
#            CORBA.Any is resolved to object (and than converted to dict as well).
#        '''
#        if isinstance(corba_obj, CORBA.Any):
#            corba_obj = from_any(corba_obj, True)
#        if type(corba_obj) in types.StringTypes:
#            return corba_obj.decode(self.coding)
#        if type(corba_obj) in self.BasicTypes:
#            return corba_obj
#        elif type(corba_obj) in self.IterTypes:
#            return [ self.decode_to_dict(x) for x in corba_obj ]
#        elif type(corba_obj) == types.InstanceType:
#            obj_dict = dict(corba_obj.__dict__)
#            for key, val in obj_dict:
#                obj_dict[key] = self.decode_to_dict(val)
#            return obj_dict