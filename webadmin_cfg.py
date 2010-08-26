# -*- coding: utf-8 -*-

import logging

debug = False
#debug = False
caching_filter_form_javascript = True # if this settings is on, then when doing changes to filter form, you should erase all sessions, because old filter forms are still in session

www_dir = '/home/glin/programming/workspace/webadmin/www/'
locale_dir = '/home/glin/programming/workspace/webadmin/locale/'
sessions_dir = '/home/glin/programming/workspace/webadmin/sessions/'
log_dir = '/home/glin/programming/workspace/webadmin/log/'
log_level = logging.DEBUG
# logging_actions_enabled: Iff false no user actions are logged to logd.
# viewing_actions_enabled: Iff false, users cannot display log screen in
#                          Daphne.
# force_critical_logging: Iff False, any logger-related failure will silently
#                         be ignored. Iff True, failures will shoot Daphne
#                         down.
audit_log = {
    'logging_actions_enabled': True,
    'viewing_actions_enabled': True,
    'force_critical_logging' : True 
}

# enable_checking: Iff false, no security policy is enforced (there is
#                  no authorization).
# backend: Select from 'csv', 'nicauth' to specify the backend for permission
#          data.
# csv_file: Used only when 'csv' backend is selected. Speicfy the path to the
#           file with permissions.
#           File row format: username,action1.object1,action2.object2...
#           e.g.: testuser,read.domain,write.registrar,read.registrar...
permissions = {
    'enable_checking': False,
    'backend': 'csv', #, 'nicauth'
    'csv_file': 'DU_DATAROOTDIR/perms.csv',
}


idl = '/home/glin/programming/svn_enum_checkout/enum/idl/trunk/idl/ccReg.idl'
#idl = '/home/glin/programming/nic/webadmin/servers/idl_devel/idl/ccReg.idl'
#idl = '/home/glin/programming/nic/webadmin/servers/idl_trunk/idl/ccReg.idl' 

iors = (#(label, nshost, nscontext),
        (u'localní', 'localhost:20001', 'fred'),
        (u'maňásek-tom', 'hal9000', 'fred-tom'),
        (u'maňásek', 'hal9000', 'fred'),
        (u'glin-server-maňásek-name-glin', 'jsadek', 'fred-glin'),
        (u'hokuston2', 'pokuston', 'fred2'), 
        (u'hokuston', 'pokuston:32346', 'fred'),
        (u'koliha', 'curlew', 'fred'),
        (u'jarahp', 'jarahp:22346', 'fred'),
        (u'jura', '172.20.20.121', 'fred'),
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
# Date format for edit fields
js_calendar_date_format_edit = 'YYYY-MM-DD'

cherrycfg = {
    'global': {
        'server.socket_port': 18456,
        'server.socket_host': "0.0.0.0",
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


