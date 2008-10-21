from distutils.version import StrictVersion
from distutils.dir_util import mkpath
from distutils import util
from distutils import log
from distutils.file_util import copy_file

from freddist.core import setup
from freddist.command.install import install
from freddist.command.install_lib import install_lib
from freddist.command.install_data import install_data
from freddist.command.install_scripts import install_scripts
from freddist.file_util import *

import os
import sys
import re
import types

def njoin(*args):
    return os.path.normpath('/'.join(args))


PROJECT_NAME = 'fred-webadmin'
PACKAGE_NAME = 'fred_webadmin'
PACKAGE_VERSION = '3.1'

SHARE_DOC = njoin('share', 'doc', PROJECT_NAME)
SHARE_PACKAGE = njoin('share', PROJECT_NAME)
SHARE_WWW = njoin(SHARE_PACKAGE, 'www')
SHARE_LOCALE = njoin(SHARE_PACKAGE, 'locale')
SESSION_DIR = 'lib/fred_webadmin/sessions'

CONFIG_DIR = 'fred/'
INIT_DIR = 'init.d/'
BIN_DIR = 'sbin/'

EXCLUDE_FILES = ['.svn']

DEFAULT_NSCONTEXT = 'fred'
DEFAULT_NSHOST = 'localhost'
DEFAULT_NSPORT = '2809'
DEFAULT_WEBADMINPORT = '18456'

class FredWebAdminInstall(install):
    user_options = []
    user_options.extend(install.user_options)
    user_options.extend([
        ('nscontext=', None, 'CORBA nameservice context name [fred]'),
        ('nshost=', None, 'CORBA nameservice host [localhost]'),
        ('nsport=', None, 'Port where CORBA nameservice listen [2809]'),
        ('webadminport=', None, 'Port of fred-webadmin  [18456]'),
        ('ldapserver=', None, 'LDAP server'),
        ('ldapscope=', None, 'LDAP scope'),
        #('nodepcheck',  None, 'Install script will not check for dependencies.'), 
        ("idldir=",  "d", "directory where IDL files reside [PREFIX/share/idl/fred/]"),
    ])

    # boolean_options = install.boolean_options
    # boolean_options.append('nodepcheck')
    
    def initialize_options(self):
        install.initialize_options(self)

        self.idldir = None
        self.nscontext = DEFAULT_NSCONTEXT
        self.nshost = DEFAULT_NSHOST
        self.nsport = DEFAULT_NSPORT
        self.webadminport = DEFAULT_WEBADMINPORT
        self.ldapserver = ''
        self.ldapscope = ''
        self.authentization = 'CORBA'
        #self.nodepcheck = None
        
    def finalize_options(self):
        install.finalize_options(self)
        if not self.idldir:
            self.idldir = njoin(self.getDir('datarootdir'), 'idl', 'fred')
        
        self.idldir = self.idldir.rstrip('/') # remove trailing slash

    def check_simplejson(self):
        try:
            import simplejson
        except ImportError, msg:
            sys.stderr.write('ImportError: %s\n fred-webadmin needs simplejson module.\n'%msg)
            sys.exit(1)
    
    def check_CORBA(self):
        try:
            from omniORB import CORBA
        except ImportError, msg:
            sys.stderr.write('ImportError: %s\n fred-webadmin needs omniORB module.\n'%msg)
            sys.exit(1)
            
    def check_dns(self):
        try:
            import dns
        except ImportError, msg:
            sys.stderr.write('ImportError: %s\n fred-webadmin needs dnspython module.\n'%msg)
            sys.exit(1)

    def check_cherrypy(self):
        try:
            import cherrypy
        except ImportError, msg:
            sys.stderr.write('ImportError: %s\n fred-webadmin needs cherrypy version 3.x module.\n'%msg)
            sys.exit(1)
        
        cherrypy_version =  StrictVersion(cherrypy.__version__)
        if cherrypy_version < '3.0.0' or cherrypy_version >= '4.0.0':
            sys.stderr.write('ImportError: \n fred-webadmin needs cherrypy version 3.x module.\n')
            sys.exit(1)

    def check_dependencies(self):
        'Check all dependencies'
        self.check_simplejson()
        self.check_CORBA()
        self.check_dns()
        self.check_cherrypy()

    def run(self):
        #if not self.nodepcheck:
        if not self.no_check_deps:
            print 'Checking dependencies.'
            self.check_dependencies()

        install.run(self)
        
        #self.update_config_and_run_file()
        #mkpath(njoin(self.root, self.localstatedir, SESSION_DIR))

class FredWebAdminInstallLib(install_lib):
    def update_config_py(self):
        values = [((r'(sys\.path\.insert\(0, )\'[\/\w\ \.]*\'\)',
            r"\1'%s')" % os.path.join(self.getDir('sysconfdir'), 'fred')))]
        self.replace_pattern(os.path.join(self.build_dir, PACKAGE_NAME, 'config.py'),
                None, values)
        print "config.py file has been updated."

    def run(self):
        self.update_config_py()
        install_lib.run(self)
        
class FredWebAdminInstallData(install_data):
    user_options = install_data.user_options
    user_options.extend([
        ('nscontext=', None, 'CORBA nameservice context name [fred]'),
        ('nshost=', None, 'CORBA nameservice host [localhost]'),
        ('nsport=', None, 'Port where CORBA nameservice listen [2809]'),
        ('webadminport=', None, 'Port of fred-webadmin  [18456]'),
        ("idldir=",  "d", "directory where IDL files reside [PREFIX/share/idl/fred/]"),
        ('ldapserver=', None, 'LDAP server'),
        ('ldapscope=', None, 'LDAP scope'),
    ])
    def initialize_options(self):
        install_data.initialize_options(self)
        self.nscontext = None
        self.nshost = None
        self.nsport = None
        self.webadminport = None
        self.idldir = None
        self.ldapserver = None
        self.ldapscope = None
        self.authentization = None

    def finalize_options(self):
        self.set_undefined_options('install',
                ('nscontext', 'nscontext'),
                ('nshost', 'nshost'),
                ('nsport', 'nsport'),
                ('webadminport', 'webadminport'),
                ('idldir', 'idldir'),
                ('ldapserver', 'ldapserver'),
                ('ldapscope', 'ldapscope'),
        )
        
        install_data.finalize_options(self)
        if self.ldapserver and self.ldapscope:
            self.authentization = 'LDAP'
        else:
            self.authentization = 'CORBA'


    def update_webadmin_cfg(self):
        values = []
        values.append(('DU_IDL_DIR', self.idldir))
        values.append(('DU_DATAROOTDIR', self.getDir('datarootdir')))
        values.append(('DU_LOCALSTATEDIR', self.getDir('localstatedir')))
        values.append(('DU_NS_HOST', self.nshost+':'+self.nsport))
        values.append(('DU_NS_CONTEXT', self.nscontext))
        values.append(('DU_WEBADMIN_PORT', self.webadminport))
        values.append(('DU_AUTHENTICATION', self.authentization))
        values.append(('DU_LDAP_SERVER', self.ldapserver))
        values.append(('DU_LDAP_SCOPE', self.ldapscope))

        self.replace_pattern(
                os.path.join(self.srcdir, 'webadmin_cfg.py.install'),
                os.path.join('build', 'webadmin_cfg.py'), values)
        print "webadmin_cfg.py files has been updated"

    def update_fred_webadmin(self):
        values = []
        values.append(('DU_PYTHON_PATHS', "'%s', '%s'" % (os.path.join(
                self.getDir('sysconfdir'), 'fred'),
                self.getDir('purelibdir'))))

        self.replace_pattern(
                os.path.join(self.srcdir, 'fred-webadmin.install'),
                os.path.join('build', 'fred-webadmin'), values)
        print "fred-webadmin script has been updated"

    def update_webadmin_server(self):
        values = []
        values.append(('DU_PREFIX', self.getDir('prefix')))
        self.replace_pattern(
                os.path.join(self.srcdir, 'fred-webadmin-server.install'),
                os.path.join('build', 'fred-webadmin-server'),
                values)
        print "fred-webadmin-server script has been udpated"

    def run(self):
        self.update_webadmin_cfg()
        self.update_fred_webadmin()
        self.update_webadmin_server()
        install_data.run(self)

def main(directory):
    if len(directory) == 0:
        cut = 0
    else:
        cut = directory.count(os.path.sep) + 1
    try:
        setup(name = PROJECT_NAME,
              description = 'Admin Interface for FRED (Fast Registry for Enum and Domains)',
              author = 'David Pospisilik, Tomas Divis, CZ.NIC',
              author_email = 'tdivis@nic.cz',
              url = 'http://www.nic.cz',
              version = PACKAGE_VERSION,
              packages = [PACKAGE_NAME] + all_subpackages_in(PACKAGE_NAME),
              package_dir = {PACKAGE_NAME: PACKAGE_NAME},
              data_files = [
                  ('LOCALSTATEDIR/log',),
                  (os.path.join('LOCALSTATEDIR', 'lib', PROJECT_NAME, 'sessions'),),
                  ('SBINDIR', ['build/fred-webadmin']),
                  ('SYSCONFDIR/init.d', ['build/fred-webadmin-server']),
                  ('SYSCONFDIR/fred', ['build/webadmin_cfg.py']),
                  ]
              # + all_files_in(
                  # os.path.join('DATAROOTDIR', PROJECT_NAME, 'www'),
                  # os.path.join(directory, 'www'),
                  # cutSlashes_dst=cut
                  # )
              # + all_files_in(
                  # os.path.join('DATAROOTDIR', PROJECT_NAME, 'locale'),
                  # os.path.join(directory, 'locale'),
                  # cutSlashes_dst=cut
                  # ),
                  + all_files_in_4(
                      os.path.join('DATAROOTDIR', PROJECT_NAME, 'locale'),
                      os.path.join(directory, 'locale'))
                  + all_files_in_4(
                      os.path.join('DATAROOTDIR', PROJECT_NAME, 'www'),
                      os.path.join(directory, 'www')),
              cmdclass = {
                          'install': FredWebAdminInstall,
                          'install_data': FredWebAdminInstallData,
                          'install_lib': FredWebAdminInstallLib,
                         },
        )
        return True
    except Exception, e:
        log.error("Error: %s", e)
        return False
    
if __name__ == '__main__':
    dir = ''
    if 'bdist' in sys.argv:
        dir = ''
    else:
        dir = os.path.dirname(sys.argv[0])
    if main(dir):
        print "All done!"
