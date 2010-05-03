# -*- coding: utf-8 -*-

import logging

#debug = True
debug = False
caching_filter_form_javascript = True # if this settings is on, then when doing changes to filter form, you should erase all sessions, because old filter forms are still in session

www_dir = '/home/tomas/code/enum/webadmin/trunk/www/'
locale_dir = '/home/tomas/code/enum/webadmin/trunk/locale/'
sessions_dir = '/home/tomas/code/enum/webadmin/trunk/sessions/'
log_dir = '/home/tomas/code/enum/webadmin/trunk/'
log_level = logging.ERROR

# logging_actions_enabled: Iff false no user actions are logged to logd.
# viewing_actions_enabled: Iff false, users cannot display log screen in
#                          Daphne.
# force_critical_logging: Iff False, any logger-related failure will silently
#                         be ignored. Iff True, failures will shoot Daphne
#                         down.
audit_log = {
    'logging_actions_enabled': True,
    'viewing_actions_enabled': True,
    'force_critical_logging' : False 
}

permissions = {
    'enable_checking': True,
    'backend': 'csv', #, 'nicauth'
    'csv_file': 'perms.csv',
}

idl = '/usr/local/share/idl/fred/ccReg.idl' #'/usr/share/idl/fred/ccReg.idl'
iors = (#(label, nshost, nscontext),
		('Test', 'localhost:2809', 'fred'),
	   )

tablesize = 45

auth_method = 'CORBA' # 'LDAP', 'CORBA', 'OPENID'
LDAP_server = 'ldap.nic.cz'
LDAP_scope = 'uid=%s,ou=People,dc=nic,dc=cz'

# gettext
gettext_domain = 'adif'
localepath = locale_dir
#lang = 'cs_CZ'
lang = 'en_US'

js_calendar_date_format = 'D.M.YYYY'
# Date format for edit fields
js_calendar_date_format_edit = 'YYYY-MM-DD'

cherrycfg = {
    'global': {
        'server.socket_port': 22353,
        'server.socket_host': "0.0.0.0",
        'server.thread_pool': 10,
        'logDebugInfoFilter.on': False, 
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


