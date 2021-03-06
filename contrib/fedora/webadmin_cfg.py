# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2019  CZ.NIC, z. s. p. o.
#
# This file is part of FRED.
#
# FRED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FRED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FRED.  If not, see <https://www.gnu.org/licenses/>.

################################################################################
#              FRED WebAdmin (Daphne) Configuration File                       #
################################################################################
import logging

# Display of debug messages
# debug = True
debug = False

# Search filter caching
# The structure of a search filter is generated to a file dynamically.
# If True, the file is cached (faster application).
# If False, the file is re-generated each time and therefore changes
# can be seen immediately without logging out or deleting sessions.
caching_filter_form_javascript = True

# Path to static files (used in CherryPy configuration)
www_dir = '/usr/lib/python2.7/site-packages/fred_webadmin/www/'
# Path to localization directories (used in gettext configuration)
locale_dir = '/usr/lib/python2.7/site-packages/fred_webadmin/locale'
# Path to the directory for storing web sessions
sessions_dir = '/var/lib/fred-webadmin/sessions/'
# Path to the directory of the log file
log_dir = '/var/log/fred-webadmin/'
# The minimum severity level of log messages going to the log file
log_level = logging.ERROR

### Settings of logd logging
audit_log = {
    # If False, user actions are not logged to logd
    'logging_actions_enabled': True,
    # If False, users cannot view the log section in Daphne
    'viewing_actions_enabled': True,
    # If False, any logger-related failure will silently be ignored.
    # If True, failures will shoot Daphne down.
    'force_critical_logging': True,
}

### Authorization settings
permissions = {
    # If False, no security policy is enforced (there is no authorization)
    'enable_checking': False,
    # Select the backend for permission data - 'csv' or 'nicauth'
    'backend': 'csv',  # , 'nicauth'
    # Path to the file with permissions (used only with 'csv' backend)
    # File row format: username,action1.object1,action2.object2...
    # e.g.: testuser,read.domain,write.registrar,read.registrar...
    'csv_file': '/usr/share/perms.csv',
}

# List (tuple) of backends (FRED servers) available for login
# Each backend is a tuple (label, nshost, nscontext) where:
# label - the label displayed in the drop-down menu on the login screen,
# nshost - CORBA naming service address[:port],
# nscontext - CORBA context.
# NOTE The connection works only for FRED servers
#      with the same version of IDL files.
iors = (('Fred', 'localhost:2809', 'fred'),)

### Result table settings
# Number of rows per page of the result table
table_page_size = 45
# Filter timeout in miliseconds
# If results aren't returned in time, the user is asked to restrict the query
table_timeout = 10000 # ms
# General limit for the total number of rows in result tables
# (default for all objects unless specified otherwise)
table_max_row_limit = 1000
# Object-specific limits for the total number of rows
# (override the general limit)
table_max_row_limit_per_obj = {
    # Maximum number of rows in the table of domains
    'domain': 2000,
    # Available keys: 'registrar', 'domain', 'invoice',
    # 'contact', 'nsset', 'keyset', 'file', 'logger', 'mail', 'message',
    # 'filter', 'publicrequest'
}

### Authentication settings
# Method:
# * 'CORBA' - dummy login (any username and password)
# * 'LDAP' - login using LDAP username and password
auth_method = 'CORBA'
# Address of the LDAP server
LDAP_server = ''
# LDAP scope string (should contain %s that will be replaced by the username)
LDAP_scope = ''

### Localization settings (gettext)
# Domain name (selects the *.mo file)
gettext_domain = 'adif'
# Root directory for localizations
localepath = locale_dir
# Language to be used
# lang = 'cs_CZ'
lang = 'en_US'
timezone = 'Europe/Prague'

# Memory-caching server address (host:port)
memcached_server = '127.0.0.1:11211'

# Date format for display in the calendar
js_calendar_date_format = 'D.M.YYYY'
# Date format for edit fields
js_calendar_date_format_edit = 'YYYY-MM-DD'

# Month count to calculate termination date in blocking/blacklisting forms
# (Javascript links "now + X month(s)")
blocking_link_add_month_count = 4
blacklisting_link_add_month_count = 1

### Administrative verification settings
# Default lock duration for resolving a verification check
verification_check_lock_default_duration = 5 * 60  # seconds
# Limit of the wait for a reaction to a manual verification check request
# (Used to calculate the "To resolve since" date)
verification_check_manual_waiting = 30  # days

### CherryPy configuration
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
        'tools.sessions.timeout': 60,  # in minutes
        'log.screen': False,
        'log.access_file': '',
        'log.error_file': '',
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

# Path to the file with Logger property names
properties_file = '/etc/fred/webadmin_logger_property_names.txt'
