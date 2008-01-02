#!/usr/bin/python
# -*- coding: utf-8 -*-


debug = True
caching_filter_form_javascript = False # if this settings is on, then when doing changes to filter form, you should erase all sessions, because old filter forms are still in session

def curdir(f = ''):
    import os.path
    return os.path.join(os.path.dirname(__file__), f) # in globlal module builtin variable __file__ is path, from which was program executed
#base_dir = curdir()
base_dir = '/home/glin/programming/workspace/cherry_admin'


idl = '/home/glin/programming/svn_enum_checkout/enum/idl/trunk/ccReg.idl'
iors = ('corbaname::pokuston', 'corbaname::curlew')

# additional program files location (corba.py, corbaparser.py, exposed.py, ..)
lib_path = base_dir + '/lib'


title = 'SUMO2 / CherryPy'
tablesize = 45

# gettext
gettext_domain = 'adif'
localepath = base_dir + '/locale'
lang = 'cs_CZ'
#lang = 'en_US'


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
        'tools.sessions.storage_path': base_dir + '/sessions',
        'tools.sessions.timeout': 60, # in minutes
        'server.log_to_screen': False,
        'server.log_file': base_dir + '/access.log',
    },
    '/': {'tools.staticdir.root':  base_dir + "/data"},
    '/css': {'tools.staticdir.on': True,
             'tools.staticdir.dir': 'css'},
    '/js': {'tools.staticdir.on': True,
            'tools.staticdir.dir': 'js'},
    '/img': {'tools.staticdir.on': True,
             'tools.staticdir.dir': 'img'},
    '/favicon.ico': {'tools.staticfile.on': True,
                     'tools.staticfile.filename': '/home/glin/programming/workspace/cherry_admin/data/img/favicon.png'}
}


