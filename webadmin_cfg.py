# -*- coding: utf-8 -*-

import logging

debug = True
caching_filter_form_javascript = True # if this settings is on, then when doing changes to filter form, you should erase all sessions, because old filter forms are still in session


def curdir(f = ''):
    import os.path
    return os.path.join(os.path.dirname(__file__), f) # in globlal module builtin variable __file__ is path, from which was program executed
base_dir = curdir()
#base_dir = '/home/glin/programming/workspace/webadmin/'
www_dir = base_dir + "www/"
sessions_dir = base_dir + 'sessions/'
locale_dir = base_dir + 'locale/'
log_dir = base_dir
log_level = logging.DEBUG

#idl = '/home/glin/programming/svn_enum_checkout/enum/idl/trunk/ccReg.idl'
idl = '/home/glin/programming/nic/webadmin/servers/idl_devel/idl/ccReg.idl'

iors = (#(label, nshost, nscontext),
        (u'localní', 'localhost', 'fred'),
        (u'maňásek', 'jsadek', 'fred'),
        (u'hokuston2', 'pokuston', 'fred2'), 
        (u'hokuston', 'pokuston', 'fred'), 
        (u'koliha', 'curlew', 'fred'),
        (u'jarahp', 'jarahp:22346', 'fred'),
       ) 

auth_method = 'LDAP' # 'LDAP', 'CORBA'
LDAP_server = 'ldap.office.nic.cz'
LDAP_scope = 'uid=%s,ou=People,dc=nic,dc=cz'

tablesize = 45

# gettext
gettext_domain = 'adif'
localepath = locale_dir
lang = 'cs_CZ'
#lang = 'en_US'

js_calendar_date_format = 'D.M.YYYY'

cherrycfg = {
    'global': {
        'server.socket_port': 18456,
        'server.socket_host': "",
        'server.thread_pool': 10,
        'server.environment': 'production',
        'tools.decode.on': True,
        'tools.decode.encoding': 'utf-8',
        'tools.encode.on': True,
        'tools.encode.encoding': 'utf-8',
        'tools.sessions.on': True,
        'tools.sessions.storage_type': 'file',
        'tools.sessions.storage_path': sessions_dir,
        'tools.sessions.timeout': 60 * 5, # in minutes
        'server.log_to_screen': False,
        'server.log_file': log_dir + 'fred_webadmin.log',
    },
    '/': {'tools.staticdir.root':  www_dir},
    '/css': {'tools.staticdir.on': True,
             'tools.staticdir.dir': 'css'},
    '/js': {'tools.staticdir.on': True,
            'tools.staticdir.dir': 'js'},
    '/img': {'tools.staticdir.on': True,
             'tools.staticdir.dir': 'img'},
    '/favicon.ico': {'tools.staticfile.on': True,
                     'tools.staticfile.filename': www_dir + 'img/favicon.png'}
}


