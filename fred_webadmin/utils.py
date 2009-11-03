import datetime
import cherrypy
from cherrypy.lib import http
import simplejson
from omniORB.any import from_any
from logging import debug

from corba import ccReg, Registry
from corba import CorbaServerDisconnectedException
from mappings import f_name_enum#, f_objectType_name
from mappings import f_enum_name


# recoder of CORBA objects
from corbarecoder import CorbaRecode
recoder = CorbaRecode('utf-8')
c2u = recoder.decode # recode from corba string to unicode
u2c = recoder.encode # recode from unicode to strings

def json_response(data):
    ''' Sets cherrypy contentype of response to text/javascript and return data as JSON '''
    cherrypy.response.headers['Content-Type'] = 'text/javascript'
    return simplejson.dumps(data) 

"""class LateBindingProperty(property) :
    __doc__ = property.__dict__['__doc__'] # see bug #576990

    def __init__(self, fget=None, fset=None, fdel=None, doc=None) :
        if fget: 
            fget = lambda s, n=fget.__name__ : getattr(s, n)()
        if fset: 
            fset = lambda s, v, n=fset.__name__ : getattr(s, n)(v)
        if fdel: 
            fdel = lambda s, n=fdel.__name__ : getattr(s, n)()
        property.__init__(self, fget, fset, fdel, doc)"""
"""
class LateBindingProperty(object):
    def __init__(self, getname=None, setname=None, delname=None,
                 doc=None):
        self.getname = getname.__name__ if getname is not None else None
        self.setname = setname.__name__ if setname is not None else None
        self.delname = delname.__name__ if delname is not None else None
        self.__doc__ = doc

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.getname is None:
            raise AttributeError('unreadable attribute')
        try:
            fget = getattr(obj, self.getname)
        except AttributeError:
            raise TypeError('%s object does not have a %s method' %
                            (type(obj).__name__, self.getname))
        return fget()

    def __set__(self, obj, value):
        if self.setname is None:
            raise AttributeError("can't set attribute")
        try:
            fset = getattr(obj, self.setname)
        except AttributeError:
            raise TypeError('%s object does not have a %s method' %
                            (type(obj).__name__, self.setname))
        fset(value)

    def __delete__(self, obj):
        if self.delname is None:
            raise AttributeError("can't delete attribute")
        try:
            fdel = getattr(obj, self.delname)
        except AttributeError:
            raise TypeError('%s object does not have a %s method' %
                            (type(obj).__name__, self.delname))
        fdel()
"""


def update_meta (self, other):
    """ Taken from http://code.activestate.com/recipes/408713/ """
    self.__name__ = other.__name__
    self.__doc__ = other.__doc__
    self.__dict__.update(other.__dict__)
    return self


class LateBindingProperty (property):
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


def get_current_url(request = None):
    ''' Returns requested url of request. '''
    if request is None:
        request = cherrypy.request
    addr = request.path_info

    if request.query_string:
        addr += '?' + request.query_string
    return addr

def append_getpar_to_url(url=None, add_par_dict = None, del_par_list = None):
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


details_cache = {}
def get_detail(obj_type_name, obj_id):
#    from webwidgets.gpyweb.gpyweb import DictLookup
#    if obj_type_name == 'domain' and obj_id == 41:
#        from omniORB.any import to_any
#        return dict(id=41L, fqdn=u'yes.cz', 
#                    roid=u'D0000000041-CZ', 
#                    registrar=Registry.OID(1, 'TESTING-REG-HANDLE', ccReg.FT_REGISTRAR),
#                    createDate=u'28.05.2008 16:48:28', transferDate=u'', updateDate=u'', 
#                    createRegistrarHandle=u'REG-UNITTEST3', updateRegistrarHandle=u'', 
#                    authInfo=[
#                        Registry.HistoryRecord(to_any(u'pEklw2iU'), 3, ccReg.DateTimeType(ccReg.DateType(1, 1, 2007), 16, 10, 11), ccReg.DateTimeType(ccReg.DateType(0, 0, 0), 16, 10, 12)), 
#                        Registry.HistoryRecord(to_any(u'pEklw2iU'), 3, ccReg.DateTimeType(ccReg.DateType(1, 6, 2006), 16, 10, 10), ccReg.DateTimeType(ccReg.DateType(1, 1, 2007), 16, 10, 11)), 
#                    ], 
#                    registrantHandle=u'CID:TOM', expirationDate=u'28.05.2009', valExDate=u'', nssetHandle=u'',
#                    admins=[
#                            Registry.OID(6, 'CID:Manasek', ccReg.FT_CONTACT),
#                            Registry.OID(6, 'CID:Tirno', ccReg.FT_CONTACT),
#                    ],
#                    admin_pets=[
#                            Registry.HistoryRecord(to_any([
#                                Registry.OID(6, 'CID:Racca', ccReg.FT_CONTACT),
#                                Registry.OID(6, 'CID:Caka', ccReg.FT_CONTACT),
#                            ]), 3, ccReg.DateTimeType(ccReg.DateType(1, 1, 2008), 16, 10, 11), ccReg.DateTimeType(ccReg.DateType(0, 0, 0), 0, 0, 0)),
#                            Registry.HistoryRecord(to_any([
#                                Registry.OID(8, 'CID:Osvald', ccReg.FT_CONTACT),
#                                Registry.OID(6, 'CID:Olina', ccReg.FT_CONTACT),
#                            ]), 3, ccReg.DateTimeType(ccReg.DateType(2, 1, 2007), 16, 10, 12), ccReg.DateTimeType(ccReg.DateType(3, 1, 2007), 16, 10, 12)),
#                            Registry.HistoryRecord(to_any([
#                                Registry.OID(23, 'CID:Goro', ccReg.FT_CONTACT),
#                                Registry.OID(8, 'CID:Mourek', ccReg.FT_CONTACT),
#                            ]), 3, ccReg.DateTimeType(ccReg.DateType(1, 1, 2007), 16, 10, 11), ccReg.DateTimeType(ccReg.DateType(2, 1, 2007), 16, 10, 12)),
#                    ],
#                    
#                    temps=[
#                            Registry.HistoryRecord(to_any(Registry.OID(6, 'CID:Racca',   ccReg.FT_CONTACT)), 3, ccReg.DateTimeType(ccReg.DateType(3, 3, 2007), 16, 10, 12), ccReg.DateTimeType(ccReg.DateType(0, 0, 0), 0, 0, 0)),
#                            Registry.HistoryRecord(to_any(Registry.OID(9, 'CID:Osvald', ccReg.FT_CONTACT)), 3, ccReg.DateTimeType(ccReg.DateType(2, 2, 2007), 16, 10, 12), ccReg.DateTimeType(ccReg.DateType(3, 3, 2007), 16, 10, 12)),
#                            Registry.HistoryRecord(to_any(Registry.OID(23, 'CID:Goro',  ccReg.FT_CONTACT)), 3, ccReg.DateTimeType(ccReg.DateType(1, 1, 2007), 16, 10, 11), ccReg.DateTimeType(ccReg.DateType(2, 2, 2007), 16, 10, 12)),
#                    ], 
#                    statusList=[15])
    result_from_cache = details_cache.get((obj_type_name, obj_id))
    if result_from_cache is not None:
        debug('Cache hit (%s, %s)' % (obj_type_name, obj_id))
        return result_from_cache

    debug('Getting detail %s id %s' % (obj_type_name, obj_id))
    corba_session = get_corba_session()
    c_any = corba_session.getDetail(f_name_enum[obj_type_name], u2c(obj_id))
    corba_obj = from_any(c_any, True)
    result = c2u(corba_obj)
    debug('Getting detail %s id %s done' % (obj_type_name, obj_id))
    
    details_cache[(obj_type_name, obj_id)] = result
    return result


def get_detail_from_oid(oid):
    if oid:
        #return get_detail(f_objectType_name[oid.type], oid.id)
        return get_detail(f_enum_name[oid.type], oid.id)
    
    
def date_to_corba(date):
    'parametr date is datetime.date() or None, and is converted to ccReg.DateType. If date is None, then ccReg.DateType(0, 0, 0) is returned' 
    return date and ccReg.DateType(*reversed(date.timetuple()[:3])) or ccReg.DateType(0, 0, 0)

def corba_to_date(corba_date):
    if corba_date.year == 0: # empty date is in corba = DateType(0, 0, 0)
        return None
    return datetime.date(corba_date.year, corba_date.month, corba_date.day)


def datetime_to_corba(date_time):
    if date_time:
        t_tuple = date_time.timetuple()
        return ccReg.DateTimeType(ccReg.DateType(*reversed(t_tuple[:3])), *t_tuple[3:6])
    else:
        return ccReg.DateTimeType(ccReg.DateType(0, 0, 0), 0, 0, 0)

def corba_to_datetime(corba_date_time):
    corba_date = corba_date_time.date
    if corba_date.year == 0: # empty date is in corba = DateType(0, 0, 0)
        return None
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
        corba_interval = interval_type(c_day, c_to, ccReg.DAY, val[4] or 0) # c_to will be ignored
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
