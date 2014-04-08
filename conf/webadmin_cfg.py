# -*- coding: utf-8 -*-
import logging

#debug = True
debug = False

# If this settings is on, then when doing changes to filter form,
# you should erase all sessions, because old filter forms are still
# in session.
caching_filter_form_javascript = True

www_dir = 'DU_DATAROOTDIR/fred-webadmin/www/'
locale_dir = 'DU_LOCALE_DIR'
sessions_dir = 'DU_LOCALSTATEDIR/lib/fred-webadmin/sessions/'
log_dir = 'DU_LOCALSTATEDIR/log/fred-webadmin/'
log_level = logging.ERROR

# logging_actions_enabled: If false no user actions are logged to logd.
# viewing_actions_enabled: If false, users cannot display log screen in
#                          Daphne.
# force_critical_logging: If False, any logger-related failure will silently
#                         be ignored. If True, failures will shoot Daphne
#                         down.
audit_log = {
    'logging_actions_enabled': True,
    'viewing_actions_enabled': True,
    'force_critical_logging': True,
}

# enable_checking: If false, no security policy is enforced (there is
#                  no authorization).
# backend: Select from 'csv', 'nicauth' to specify the backend for permission
#          data.
# csv_file: Used only when 'csv' backend is selected. Speicfy the path to the
#           file with permissions.
#           File row format: username,action1.object1,action2.object2...
#           e.g.: testuser,read.domain,write.registrar,read.registrar...
permissions = {
    'enable_checking': False,
    'backend': 'csv',  # , 'nicauth'
    'csv_file': 'DU_DATAROOTDIR/perms.csv',
}

# '/usr/share/idl/fred/ccReg.idl'
idl = 'DU_IDL_DIR/ccReg.idl'
# (label, nshost, nscontext),
iors = (('Fred', 'DU_NS_HOST', 'DU_NS_CONTEXT'),)

table_page_size = 45
table_timeout = 10000

# default max row limit for tables
table_max_row_limit = 1000
# specific max row to override limit for particular objects:
table_max_row_limit_per_obj = {
    'domain': 2000,
}

# 'LDAP', 'CORBA'
auth_method = 'DU_AUTHENTICATION'
LDAP_server = 'DU_LDAP_SERVER'
LDAP_scope = 'DU_LDAP_SCOPE'

# gettext
gettext_domain = 'adif'
localepath = locale_dir
# lang = 'cs_CZ'
lang = 'en_US'

memcached_server = '127.0.0.1:11211'

js_calendar_date_format = 'D.M.YYYY'
# Date format for edit fields
js_calendar_date_format_edit = 'YYYY-MM-DD'

# Javascript links to set date "new + X months" for administrative domain blocking and delete & blacklist forms:
blocking_link_add_month_count = 4
blacklisting_link_add_month_count = 1

# Administrative verification - default lock duration for resolving verification check
verification_check_lock_default_duration = 5 * 60  # seconds

cherrycfg = {
    'global': {
        'server.socket_port': DU_WEBADMIN_PORT,
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
        'tools.sessions.timeout': 60,  # in minutes
        'server.log_to_screen': False,
        'server.log_file': log_dir + 'fred-webadmin.log',
    },
    '/': {'tools.staticdir.root': www_dir},
    '/css': {'tools.staticdir.on': True,
             'tools.staticdir.dir': 'css'},
    '/js': {'tools.staticdir.on': True,
            'tools.staticdir.dir': 'js'},
    '/img': {'tools.staticdir.on': True,
             'tools.staticdir.dir': 'img'},
    '/favicon.ico': {'tools.staticfile.on': True,
                     'tools.staticfile.filename': www_dir + 'img/favicon.png'}
}

properties_file = 'DU_SYSCONFDIR/fred/webadmin_logger_property_names.txt'
