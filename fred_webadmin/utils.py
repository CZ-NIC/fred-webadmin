import datetime
import logging
import cherrypy
import simplejson
from cherrypy.lib import http
from omniORB.any import from_any
from logging import debug
import CosNaming

import fred_webadmin.corbarecoder as recoder
from corba import ccReg, Registry
from corba import CorbaServerDisconnectedException
from mappings import f_name_enum#, f_objectType_name
from mappings import f_enum_name
from fred_webadmin.corba import Corba
from fred_webadmin import config
from pylogger.dummylogger import DummyLogger
from pylogger.corbalogger import Logger, LoggerFailSilent

# recoder of CORBA objects
#from corbarecoder import CorbaRecode
#recoder = CorbaRecode('utf-8')
#c2u = recoder.decode # recode from corba string to unicode
#u2c = recoder.encode # recode from unicode to strings

# one logger for each corba ior specified in config.iors
loggers = {}

def json_response(data):
    ''' Sets cherrypy contentype of response to text/javascript and return data as JSON '''
    cherrypy.response.headers['Content-Type'] = 'text/javascript'
    return simplejson.dumps(data)


def update_meta (self, other):
    """ Taken from http://code.activestate.com/recipes/408713/ """
    self.__name__ = other.__name__
    self.__doc__ = other.__doc__
    self.__dict__.update(other.__dict__)
    return self


class LateBindingProperty(property):
    """ Taken from http://code.activestate.com/recipes/408713/ """

    def __new__(cls, fget=None, fset=None, fdel=None, doc=None):

        if fget is not None:
            def __get__(obj, objtype=None, name=fget.__name__):
                fget = getattr(obj, name)
                return fget()

            fget = update_meta(__get__, fget)

        if fset is not None:
            def __set__(obj, value, name=fset.__name__):
                fset = getattr(obj, name)
                return fset(value)

            fset = update_meta(__set__, fset)

        if fdel is not None:
            def __delete__(obj, name=fdel.__name__):
                fdel = getattr(obj, name)
                return fdel()

            fdel = update_meta(__delete__, fdel)

        return property(fget, fset, fdel, doc)


def get_current_url(request=None):
    ''' Returns requested url of request. '''
    if request is None:
        request = cherrypy.request
    addr = request.path_info

    if request.query_string:
        addr += '?' + request.query_string
    return addr

def append_getpar_to_url(url=None, add_par_dict=None, del_par_list=None):
    ''' Appends HTTP GET parameters to url from add_par_dict
        and deletes HTTP GET parameters of name given in del_par_list.
        If url is not specified, current url is taken
    '''
    if url == None:
        url = cherrypy.request.path_info
        get_pars = dict(http.parse_query_string(cherrypy.request.query_string)) # copy params of current url
    else:
        get_pars = {}
        raise NotImplementedError('Appending parametr to custom url was not yet added (need to parse url)')

    if add_par_dict:
        get_pars.update(add_par_dict)

    if del_par_list:
        for par_name in del_par_list:
            if get_pars.has_key(par_name):
                get_pars.pop(par_name)

    url += '?' + '&'.join(['%s=%s' % par for par in get_pars.items()])

    return url


def get_corba_session():
    try:
        corbaSessionString = cherrypy.session.get('corbaSessionString')
        return cherrypy.session.get('Admin').getSession(corbaSessionString)
    except ccReg.Admin.ObjectNotFound:
        raise CorbaServerDisconnectedException



def _create_logger(corba_server_spec):
    """ Creates logger object to send log requests to the server.
        Returns:
            Logger object. Either DummyLogger when nothing should be
            logged, or SessionLogger (normal logging with exceptions on
            failure), or SessionLoggerFailSilent (logging that fails
            silently without exceptions).
    """
    if not config.audit_log['logging_actions_enabled']:
        logger = DummyLogger()
    else:
        logging.debug('Created Logger for server %s', config.iors[corba_server_spec])
        ior = config.iors[corba_server_spec][1]
        nscontext = config.iors[corba_server_spec][2]

        corba = Corba()
        corba.connect(ior, nscontext)
        try:
            corba_logd = corba.getObject('Logger', 'ccReg.Logger')
        except CosNaming.NamingContext.NotFound:
            if config.audit_log['force_critical_logging']:
                raise
            logger = DummyLogger()
        else:
            # CorbaLazyRequest needs to have the CORBA logd object in
            # cherrypy.session
            cherrypy.session['Logger'] = corba_logd
            if config.audit_log['force_critical_logging']:
                logger = Logger(dao=corba_logd, corba_module=ccReg)
            else:
                logger = LoggerFailSilent(dao=corba_logd, corba_module=ccReg)
    return logger

def get_logger():
    # get logger from loggers by corba_ior or create new one for it
    current_corba_server = cherrypy.session['corba_server']
    logger = loggers.get(current_corba_server)
    if not logger:
        loggers[current_corba_server] = logger = _create_logger(current_corba_server)
    return logger

def create_log_request(request_type, properties=None, references=None):
    log_req = get_logger().create_request(
        cherrypy.request.headers['Remote-Addr'], 'WebAdmin', request_type,
        properties, references, cherrypy.session.get('logger_session_id', 0)
    )
    return log_req

details_cache = {}
def get_detail(obj_type_name, obj_id, use_cache=True):
    """ If use_cache == False, we always get the object from
        server. """
    if use_cache:
        result_from_cache = details_cache.get((obj_type_name, obj_id))
        if result_from_cache is not None:
            debug('Cache hit (%s, %s)' % (obj_type_name, obj_id))
            return result_from_cache

    debug('Getting detail %s id %s' % (obj_type_name, obj_id))
    corba_session = get_corba_session()
    c_any = corba_session.getDetail(
        f_name_enum[obj_type_name], recoder.u2c(obj_id))
    corba_obj = from_any(c_any, True)
    result = recoder.c2u(corba_obj)

    details_cache[(obj_type_name, obj_id)] = result
    return result

def get_state_id_by_short_name(short_name):
    for state in cherrypy.session['Admin'].getObjectStatusDescList(config.lang[:2]):
        if state.shortName == short_name:
            return state.id


def get_detail_from_oid(oid):
    if oid:
        #return get_detail(f_objectType_name[oid.type], oid.id)
        return get_detail(f_enum_name[oid.type], oid.id)


def get_property_list(fname=None):
    if fname is None:
        fname = config.properties_file
    result = []
    for line in open(fname, 'r'):
        line = line.strip()
        result.append((line, line))
    return result

## {{{ http://code.activestate.com/recipes/576693/ (r9)
# Backport of OrderedDict() class that runs on Python 2.4, 2.5, 2.6, 2.7 and pypy.
# Passes Python2.7's test suite and incorporates all the latest updates.

try:
    from thread import get_ident as _get_ident
except ImportError:
    from dummy_thread import get_ident as _get_ident

try:
    from _abcoll import KeysView, ValuesView, ItemsView
except ImportError:
    pass


# Ordered dict for Python <2.7
class OrderedDict(dict):
    'Dictionary that remembers insertion order'
    # An inherited dict maps keys to values.
    # The inherited dict provides __getitem__, __len__, __contains__, and get.
    # The remaining methods are order-aware.
    # Big-O running times for all methods are the same as for regular dictionaries.

    # The internal self.__map dictionary maps keys to links in a doubly linked list.
    # The circular doubly linked list starts and ends with a sentinel element.
    # The sentinel element never gets deleted (this simplifies the algorithm).
    # Each link is stored as a list of length three:  [PREV, NEXT, KEY].

    def __init__(self, *args, **kwds):
        '''Initialize an ordered dictionary.  Signature is the same as for
        regular dictionaries, but keyword arguments are not recommended
        because their insertion order is arbitrary.

        '''
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        try:
            self.__root
        except AttributeError:
            self.__root = root = []                     # sentinel node
            root[:] = [root, root, None]
            self.__map = {}
        self.__update(*args, **kwds)

    def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
        'od.__setitem__(i, y) <==> od[i]=y'
        # Setting a new item creates a new link which goes at the end of the linked
        # list, and the inherited dictionary is updated with the new key/value pair.
        if key not in self:
            root = self.__root
            last = root[0]
            last[1] = root[0] = self.__map[key] = [last, root, key]
        dict_setitem(self, key, value)

    def __delitem__(self, key, dict_delitem=dict.__delitem__):
        'od.__delitem__(y) <==> del od[y]'
        # Deleting an existing item uses self.__map to find the link which is
        # then removed by updating the links in the predecessor and successor nodes.
        dict_delitem(self, key)
        link_prev, link_next, key = self.__map.pop(key)
        link_prev[1] = link_next
        link_next[0] = link_prev

    def __iter__(self):
        'od.__iter__() <==> iter(od)'
        root = self.__root
        curr = root[1]
        while curr is not root:
            yield curr[2]
            curr = curr[1]

    def __reversed__(self):
        'od.__reversed__() <==> reversed(od)'
        root = self.__root
        curr = root[0]
        while curr is not root:
            yield curr[2]
            curr = curr[0]

    def clear(self):
        'od.clear() -> None.  Remove all items from od.'
        try:
            for node in self.__map.itervalues():
                del node[:]
            root = self.__root
            root[:] = [root, root, None]
            self.__map.clear()
        except AttributeError:
            pass
        dict.clear(self)

    def popitem(self, last=True):
        '''od.popitem() -> (k, v), return and remove a (key, value) pair.
        Pairs are returned in LIFO order if last is true or FIFO order if false.

        '''
        if not self:
            raise KeyError('dictionary is empty')
        root = self.__root
        if last:
            link = root[0]
            link_prev = link[0]
            link_prev[1] = root
            root[0] = link_prev
        else:
            link = root[1]
            link_next = link[1]
            root[1] = link_next
            link_next[0] = root
        key = link[2]
        del self.__map[key]
        value = dict.pop(self, key)
        return key, value

    # -- the following methods do not depend on the internal structure --

    def keys(self):
        'od.keys() -> list of keys in od'
        return list(self)

    def values(self):
        'od.values() -> list of values in od'
        return [self[key] for key in self]

    def items(self):
        'od.items() -> list of (key, value) pairs in od'
        return [(key, self[key]) for key in self]

    def iterkeys(self):
        'od.iterkeys() -> an iterator over the keys in od'
        return iter(self)

    def itervalues(self):
        'od.itervalues -> an iterator over the values in od'
        for k in self:
            yield self[k]

    def iteritems(self):
        'od.iteritems -> an iterator over the (key, value) items in od'
        for k in self:
            yield (k, self[k])

    def update(*args, **kwds):
        '''od.update(E, **F) -> None.  Update od from dict/iterable E and F.

        If E is a dict instance, does:           for k in E: od[k] = E[k]
        If E has a .keys() method, does:         for k in E.keys(): od[k] = E[k]
        Or if E is an iterable of items, does:   for k, v in E: od[k] = v
        In either case, this is followed by:     for k, v in F.items(): od[k] = v

        '''
        if len(args) > 2:
            raise TypeError('update() takes at most 2 positional '
                            'arguments (%d given)' % (len(args),))
        elif not args:
            raise TypeError('update() takes at least 1 argument (0 given)')
        self = args[0]
        # Make progressively weaker assumptions about "other"
        other = ()
        if len(args) == 2:
            other = args[1]
        if isinstance(other, dict):
            for key in other:
                self[key] = other[key]
        elif hasattr(other, 'keys'):
            for key in other.keys():
                self[key] = other[key]
        else:
            for key, value in other:
                self[key] = value
        for key, value in kwds.items():
            self[key] = value

    __update = update  # let subclasses override update without breaking __init__

    __marker = object()

    def pop(self, key, default=__marker):
        '''od.pop(k[,d]) -> v, remove specified key and return the corresponding value.
        If key is not found, d is returned if given, otherwise KeyError is raised.

        '''
        if key in self:
            result = self[key]
            del self[key]
            return result
        if default is self.__marker:
            raise KeyError(key)
        return default

    def setdefault(self, key, default=None):
        'od.setdefault(k[,d]) -> od.get(k,d), also set od[k]=d if k not in od'
        if key in self:
            return self[key]
        self[key] = default
        return default

    def __repr__(self, _repr_running={}):
        'od.__repr__() <==> repr(od)'
        call_key = id(self), _get_ident()
        if call_key in _repr_running:
            return '...'
        _repr_running[call_key] = 1
        try:
            if not self:
                return '%s()' % (self.__class__.__name__,)
            return '%s(%r)' % (self.__class__.__name__, self.items())
        finally:
            del _repr_running[call_key]

    def __reduce__(self):
        'Return state information for pickling'
        items = [[k, self[k]] for k in self]
        inst_dict = vars(self).copy()
        for k in vars(OrderedDict()):
            inst_dict.pop(k, None)
        if inst_dict:
            return (self.__class__, (items,), inst_dict)
        return self.__class__, (items,)

    def copy(self):
        'od.copy() -> a shallow copy of od'
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        '''OD.fromkeys(S[, v]) -> New ordered dictionary with keys from S
        and values equal to v (which defaults to None).

        '''
        d = cls()
        for key in iterable:
            d[key] = value
        return d

    def __eq__(self, other):
        '''od.__eq__(y) <==> od==y.  Comparison to another OD is order-sensitive
        while comparison to a regular mapping is order-insensitive.

        '''
        if isinstance(other, OrderedDict):
            return len(self) == len(other) and self.items() == other.items()
        return dict.__eq__(self, other)

    def __ne__(self, other):
        return not self == other

    # -- the following methods are only used in Python 2.7 --

    def viewkeys(self):
        "od.viewkeys() -> a set-like object providing a view on od's keys"
        return KeysView(self)

    def viewvalues(self):
        "od.viewvalues() -> an object providing a view on od's values"
        return ValuesView(self)

    def viewitems(self):
        "od.viewitems() -> a set-like object providing a view on od's items"
        return ItemsView(self)
## end of http://code.activestate.com/recipes/576693/ }}}


class DynamicWrapper(object):
    ''' Used for wrapping Mock objects, which cannot be put to session (pickle don't work).
        Create singleton in module, create function which returns this singleton, wrap it
        using this DynamicWrapper and it can be stored to the CherryPy session.

        >>> import pickle
        >>> from mock import Mock, call
        >>> mymock = Mock()
        >>> get_obj = lambda: mymock
        >>> obj_wrap = DynamicWrapper(get_obj)
        >>> dummy_result = obj_wrap.some_method()
        >>> obj_wrap.method_calls
        [call.some_method()]
        >>> #pickle.dumps(obj_wrap) # cannot use in doctest because function obj_wrap is not formally defined but normally it works
    '''
    def __init__(self, get_object_function):
        super(DynamicWrapper, self).__setattr__('_get_object_function', get_object_function)

    def __getattr__(self, name):
        if name == '_get_object_function':
            return super(DynamicWrapper, self).__getattr__(name)
        else:
            return getattr(self._get_object_function(), name)

    def __setattr__(self, name, value):
        setattr(self._get_object_function(), name, value)
