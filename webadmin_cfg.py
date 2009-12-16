# -*- coding: utf-8 -*-

import logging

debug = True
#debug = False
caching_filter_form_javascript = True # if this settings is on, then when doing changes to filter form, you should erase all sessions, because old filter forms are still in session

www_dir = '/home/tomas/fred/root/share/fred-webadmin/www/'
locale_dir = '/home/tomas/fred/root/share/fred-webadmin/locale/'
sessions_dir = '/home/tomas/fred/root/var/lib/fred-webadmin/sessions/'
log_dir = '/home/tomas/fred/root/var/log/fred-webadmin/'
log_level = logging.DEBUG

# SessionLogger settings
session_logging_enabled = True
#session_logging_enabled = False


idl = '/home/tomas/code/enum/idl/trunk/idl/ccReg.idl' #'/usr/share/idl/fred/ccReg.idl'
iors = (#(label, nshost, nscontext),
	#	('Test', 'localhost:22346', 'fred'),
        ('Test', 'localhost', 'fred'),
	   )

tablesize = 45

auth_method = 'CORBA' # 'LDAP', 'CORBA'
LDAP_server = ''
LDAP_scope = ''

# gettext
gettext_domain = 'adif'
localepath = locale_dir
#lang = 'cs_CZ'
lang = 'en_US'

js_calendar_date_format = 'D.M.YYYY'

cherrycfg = {
    'global': {
        'server.socket_port': 22353,
        'server.socket_host': '0.0.0.0',
        'server.thread_pool': 10,
        'server.environment': 'production',
        'tools.decode.on': True,
        'tools.decode.encoding': 'utf-8',
        'tools.encode.on': True,
        'tools.encode.encoding': 'utf-8',
        'tools.sessions.on': True,
        'tools.sessions.storage_type': 'file',
        'tools.sessions.storage_path': sessions_dir,
        'tools.sessions.timeout': 60, # in minutes
        'server.log_to_screen': False,
        'server.log_file': log_dir + 'fred-webadmin.log',
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


