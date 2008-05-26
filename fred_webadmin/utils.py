import cherrypy
import simplejson

def json_response(data):
    ''' Sets cherrypy contentype of response to text/javascript and return data as JSON '''
    cherrypy.response.headers['Content-Type'] = 'text/javascript'
    return simplejson.dumps(data) 

def get_current_url(request):
    ''' Returns requested url of request. '''
    addr = request.path_info
    if request.query_string:
        addr += '?' + request.query_string
    return addr