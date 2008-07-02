import cherrypy
import simplejson
from omniORB.any import from_any

from corba import ccReg
from corba import CorbaServerDisconnectedException
from mappings import f_name_enum, f_objectType_name

# recoder of CORBA objects
from corbarecoder import CorbaRecode
recoder = CorbaRecode('utf-8')
c2u = recoder.decode # recode from corba string to unicode
u2c = recoder.encode # recode from unicode to strings

def json_response(data):
    ''' Sets cherrypy contentype of response to text/javascript and return data as JSON '''
    cherrypy.response.headers['Content-Type'] = 'text/javascript'
    return simplejson.dumps(data) 

def get_current_url(request = None):
    ''' Returns requested url of request. '''
    if request is None:
        request = cherrypy.request
    addr = request.path_info
    if request.query_string:
        addr += '?' + request.query_string
    return addr

def append_getpar_to_url(url, getpar_string):
    ''' Appends HTTP GET parameters to url'''
    if url.find('?') != -1:
        url += '&'
    else:
        url += '?'
    url += getpar_string
    return url
    

def get_corba_session():
    try:
        corbaSessionString = cherrypy.session.get('corbaSessionString')
        return cherrypy.session.get('Admin').getSession(corbaSessionString)
    except ccReg.Admin.ObjectNotFound:
        raise CorbaServerDisconnectedException

def get_detail(obj_type_name, obj_id):
    corba_session = get_corba_session()
    c_any = corba_session.getDetail(f_name_enum[obj_type_name], u2c(obj_id))
    corba_obj = from_any(c_any, True)
    result = c2u(corba_obj)
    return result

def get_detail_from_oid(oid):
    if oid:
        return get_detail(f_objectType_name[oid.type], oid.id)
