from distutils.core import setup
from distutils.command.build import build
from distutils.command.install import install
from distutils.command.install_data import install_data
from distutils.version import StrictVersion
import os
import sys
import shutil

PACKAGE_NAME = 'fred_webadmin'
PACKAGE_VERSION = '1.0'

SHARE_DOC = os.path.join('share', 'doc', PACKAGE_NAME)
SHARE_PACKAGE = os.path.join('share', PACKAGE_NAME)
SHARE_WWW = os.path.join(SHARE_PACKAGE, 'www')
SHARE_LOCALE = os.path.join(SHARE_PACKAGE, 'locale')
BIN = '/sbin/'

EXCLUDE_FILES = ['.svn']

class FredWebAdminBuild(build):
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
        self.check_dependencies()
        build.run(self)


class FredWebAdminData(install_data):
    def run(self):
        install_data.run(self)
        config_file_example = config_file = ''
        if not self.data_files:
            return
        for path, files in self.data_files:
            if files[0] == 'webadmin_cfg.py.example':
                config_file_example = files[0]
                config_file = files[0].rsplit('.', 1)[0]  # 'webadmin_cfg.py'
                break
        
        # copy webadmin_cfg.py.example to webadmin_cfg.py, only if webadmin_cfg.py doesn't exists
        if config_file:
            print 'Configuring:'
            path_config_example =  os.path.join(self.root or '', path, config_file_example) 
            path_config = os.path.join(self.root or '', path, config_file)
            if not os.path.exists(path_config):
#                print ' No old %s found, copy new from %s' % (path_config, path_config_example)
                print ' copying %s -> %s' % (path_config_example, path_config)
                shutil.copyfile(path_config_example, path_config)
            else:
                print " Leaving old %s, look at %s for new options" % (path_config, path_config_example)


def all_files_in(dst_directory, directory):
    'Returns couples (directory, directory/file) to all files in directory (recursive)'

    paths = [] # list of couples (directory, directory/file) for all files

    for filename in os.listdir(directory):
        if filename in EXCLUDE_FILES:
            continue
        full_path = os.path.join(directory, filename)
        if os.path.isfile(full_path):
            # exclude first directory in path from dst path (this include really only what is IN directory, not (directory AND files))
            splitted_directory = directory.split(os.path.sep, 1)
            if len(splitted_directory) > 1: 
                dst_subdirectory = splitted_directory[1]
            else: # directory is only one directory yet
                dst_subdirectory = ''
            paths.append((os.path.join(dst_directory, dst_subdirectory), [full_path]))
        elif os.path.isdir(full_path):
            paths.extend(all_files_in(dst_directory, full_path))    
            
    return paths

def all_subpackages_in(package):
    'Returns all subpackages (packages in subdirectories) (recursive)'
    subpackages = []
    
    for filename in os.listdir(package):
        if filename in EXCLUDE_FILES:
            continue
        full_path = os.path.join(package, filename)
        if os.path.isdir(full_path):
            subpackages.append(full_path.replace('/', '.'))
            subpackages.extend(all_subpackages_in(full_path))
    
    return subpackages
            
             
    

if __name__ == '__main__':
    setup(name = PACKAGE_NAME,
          description = 'Admin Interface for FRED (Fast Registry for Enum and Domains)',
          author = 'David Pospisilik, Tomas Divis, CZ.NIC',
          author_email = 'tdivis@nic.cz',
          url = 'http://www.nic.cz',
          version = PACKAGE_VERSION,
          packages = [PACKAGE_NAME] + all_subpackages_in(PACKAGE_NAME),
          package_dir = {PACKAGE_NAME: PACKAGE_NAME},
          
          data_files = [('/etc/fred', ['webadmin_cfg.py.example']),
                        (BIN, ['fred-webadmin']),
                        (SHARE_DOC, ['doc/INSTALL.txt']),
                        ('/var/lib/fred_webadmin/sessions', [])] +
                        all_files_in(SHARE_WWW, 'www') +
                        all_files_in(SHARE_LOCALE, 'locale'),
          cmdclass = {'build': FredWebAdminBuild,
                      'install_data': FredWebAdminData
                     },
    )
    
