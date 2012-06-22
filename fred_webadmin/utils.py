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
