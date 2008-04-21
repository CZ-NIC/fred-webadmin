from distutils.core import setup
from distutils.command.build import build
from distutils.command.build_py import build_py
from distutils.command.install import install
from distutils.command.install_data import install_data
from distutils.version import StrictVersion
from distutils.dir_util import mkpath
from distutils import util
from distutils import log

import os
import sys
import re
import types

PACKAGE_NAME = 'fred_webadmin'
PACKAGE_VERSION = '1.0'

SHARE_DOC = os.path.join('share', 'doc', PACKAGE_NAME)
SHARE_PACKAGE = os.path.join('share', PACKAGE_NAME)
SHARE_WWW = os.path.join(SHARE_PACKAGE, 'www')
SHARE_LOCALE = os.path.join(SHARE_PACKAGE, 'locale')
SESSION_DIR = 'var/lib/fred_webadmin/sessions'

CONFIG_DIR = 'etc/fred/'
BIN_DIR = 'sbin/'

EXCLUDE_FILES = ['.svn']

DEFAULT_NSCONTEXT = 'fred'
DEFAULT_NSHOST = 'localhost'
DEFAULT_NSPORT = '2809'
DEFAULT_WEBADMINPORT = '18456'

g_srcdir = '.'


class FredWebAdminBuild(build, object):
    user_options = []
    user_options.extend(install.user_options)
    user_options.extend([
        ('nodepcheck',  None, 'Install script will not check for dependencies.'),
    ])
    
    def __init__(self, *attrs):
        super(FredWebAdminBuild, self).__init__(*attrs)

        self.nodepcheck = None
        
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
        if not self.nodepcheck:        
            self.check_dependencies()
        build.run(self)
        
class FredWebAdminBuildPy(build_py, object):
    """
    Standart distutils build_py does not support scrdir option. So Build_py class
    implements this funkcionality. This code is from 
    http://lists.mysql.com/ndb-connectors/617 
    """
    def get_package_dir(self, package):
        """
        Return the directory, relative to the top of the source
        distribution, where package 'package' should be found
        (at least according to the 'package_dir' option, if any).
        """
        global g_srcdir
        self.srcdir = g_srcdir
        path = package.split('.')

        if not self.package_dir:
            if path:
                return os.path.join(self.srcdir, apply(os.path.join, path))
            else:
                return self.srcdir
        else:
            tail = []
            while path:
                try:
                    pdir = self.package_dir['.'.join(path)]
                except KeyError:
                    tail.insert(0, path[-1])
                    del path[-1]
                else:
                    tail.insert(0, pdir)
                    return os.path.join(self.srcdir, apply(os.path.join, tail))
            else:
                # Oops, got all the way through 'path' without finding a
                # match in package_dir.  If package_dir defines a directory
                # for the root (nameless) package, then fallback on it;
                # otherwise, we might as well have not consulted
                # package_dir at all, as we just use the directory implied
                # by 'tail' (which should be the same as the original value
                # of 'path' at this point).
                pdir = self.package_dir.get('')
                if pdir is not None:
                    tail.insert(0, pdir)

                if tail:
                    return os.path.join(self.srcdir, apply(os.path.join, tail))
                else:
                    return self.srcdir
    #get_package_dir()

    def check_package(self, package, package_dir):
        if package_dir != "" and not os.path.exists(package_dir):
            os.makedirs(package_dir)
        return build_py.check_package(self, package, package_dir)

class FredWebAdminInstall(install, object):
    user_options = []
    user_options.extend(install.user_options)
    user_options.extend([
        ('idldir=',  'd', 'directory where IDL files reside [PREFIX/share/idl/fred/]'),
        ('preservepath', None, 'Preserve path in configuration file.'),
        ('nscontext=', None, 'CORBA nameservice context name [fred]'),
        ('nshost=', None, 'CORBA nameservice host [localhost]'),
        ('nsport=', None, 'Port where CORBA nameservice listen [2809]'),
        ('webadminport=', None, 'Port of fred-webadmin  [18456]'),
    ])
    
    def __init__(self, *attrs):
        super(FredWebAdminInstall, self).__init__(*attrs)

        self.preservepath = None
        self.is_bdist_mode = None
        self.idldir = None
        
        self.nscontext = DEFAULT_NSCONTEXT
        self.nshost = DEFAULT_NSHOST
        self.nsport = DEFAULT_NSPORT
        self.webadminport = DEFAULT_WEBADMINPORT
        
        for dist in attrs:
            for name in dist.commands:
                if re.match('bdist', name): #'bdist' or 'bdist_rpm'
                    self.is_bdist_mode = 1 #it is bdist mode - creating a package
                    break
            if self.is_bdist_mode:
                break
            
    def finalize_options(self):
        super(FredWebAdminInstall, self).finalize_options()
        if not self.idldir:
            self.idldir = remove_last_slash(os.path.join(self.get_actual_root(), self.prefix, 'share', 'idl', 'fred'))
        
    def update_config_and_run_file(self):
        root = remove_last_slash(self.get_actual_root())
        root_and_prefix = remove_last_slash(os.path.join(root, self.prefix))
            
        config_dir =  os.path.join(root, CONFIG_DIR)
        bin_dir = os.path.join(root, BIN_DIR)
        python_packages_dir = os.path.join(root, self.install_lib)
        
        config_file = os.path.join(config_dir, 'webadmin_cfg.py')
        bin_file = os.path.join(bin_dir, 'fred-webadmin')


        body = open(curdir('webadmin_cfg.py.install')).read()
        body = body.replace('DU_IDL_DIR', self.idldir)
        body = body.replace('DU_PREFIX', root_and_prefix)
        body = body.replace('DU_ROOT', root)
        body = body.replace('DU_NS_HOST', self.nshost + ':' + self.nsport)
        body = body.replace('DU_NS_CONTEXT', self.nscontext)
        body = body.replace('DU_WEBADMIN_PORT', self.webadminport)
        
        mkpath(config_dir)
        open(config_file, 'w').write(body)
        
        body = open(curdir('fred-webadmin.install')).read()
        body = body.replace('DU_PYTHON_PATHS', "'%s', '%s'" % (config_dir, python_packages_dir))
        mkpath(bin_dir)
        open(bin_file, 'w').write(body)
        
    def get_actual_root(self):
        '''
        Return actual root only in case if the process is not in creation of the package
        '''
        return ((self.is_bdist_mode or self.preservepath) and [''] or 
                [type(self.root) is not None and self.root or ''])[0]
        
    def run(self):
        super(FredWebAdminInstall, self).run()
        self.update_config_and_run_file()
        mkpath(os.path.join(self.get_actual_root(), SESSION_DIR))
#        config_file_example = config_file = ''
#        if not self.data_files:
#            return
#        for path, files in self.data_files:
#            if files[0] == 'webadmin_cfg.py.example':
#                config_file_example = files[0]
#                config_file = files[0].rsplit('.', 1)[0]  # 'webadmin_cfg.py'
#                break
        
#        # copy webadmin_cfg.py.example to webadmin_cfg.py, only if webadmin_cfg.py doesn't exists
#        if config_file:
#            print 'Configuring:'
#            path_config_example =  os.path.join(self.root or '', path, config_file_example) 
#            path_config = os.path.join(self.root or '', path, config_file)
#            if not os.path.exists(path_config):
##                print ' No old %s found, copy new from %s' % (path_config, path_config_example)
#                print ' copying %s -> %s' % (path_config_example, path_config)
#                shutil.copyfile(path_config_example, path_config)
#            else:
#                print " Leaving old %s, look at %s for new options" % (path_config, path_config_example)

class FredWebAdminInstallData(install_data):
    """
    This is copy of standart distutils install_data class,
    with some minor changes in run method, due to srcdir option add
    """
    def run(self):
        self.srcdir = g_srcdir
        self.mkpath(self.install_dir)
        for f in self.data_files:
            if type(f) is types.StringType:
                if os.path.exists(os.path.join('build', f)):
                    f = os.path.join('build', f)
                else:
                    f = os.path.join(self.srcdir, f)
                f = util.convert_path(f)
                if self.warn_dir:
                    self.warn("setup script did not provide a directory for "
                              "'%s' -- installing right in '%s'" %
                              (f, self.install_dir))
                # it's a simple file, so copy it
                (out, _) = self.copy_file(f, self.install_dir)
                self.outfiles.append(out)
            else:
                # it's a tuple with path to install to and a list of files
                dir = util.convert_path(f[0])
                if not os.path.isabs(dir):
                    dir = os.path.join(self.install_dir, dir)
                elif self.root:
                    dir = util.change_root(self.root, dir)
                self.mkpath(dir)

                if f[1] == []:
                    # If there are no files listed, the user must be
                    # trying to create an empty directory, so add the
                    # directory to the list of output files.
                    self.outfiles.append(dir)
                else:
                    # Copy files, adding them to the list of output files.
                    for data in f[1]:
                        #first look into ./build directory for requested
                        #data file. If this exists in build dir then
                        #use it and copy it into proper destination,
                        #otherwise use file from srcdir/
                        if os.path.exists(os.path.join('build', data)):
                            data = os.path.join('build', data)
                        else:
                            data = os.path.join(self.srcdir, data)
                        data = util.convert_path(data)
                        print data
                        (out, _) = self.copy_file(data, dir)
                        self.outfiles.append(out)

 
def remove_last_slash(path):
    if path[-1] == os.path.sep:
        path = path[:-1]
    return path

def curdir(path):
    return os.path.join(g_srcdir, path)
    
def all_files_in(dst_directory, directory):
    'Returns couples (directory, directory/file) to all files in directory (recursive)'

    paths = [] # list of couples (directory, directory/file) for all files

    for filename in os.listdir(curdir(directory)):
        if filename in EXCLUDE_FILES:
            continue
        full_path = os.path.join(directory, filename)
        if os.path.isfile(curdir(full_path)):
            # exclude first directory in path from dst path (this include really only what is IN directory, not (directory AND files))
            splitted_directory = directory.split(os.path.sep, 1)
            if len(splitted_directory) > 1: 
                dst_subdirectory = splitted_directory[1]
            else: # directory is only one directory yet
                dst_subdirectory = ''
            paths.append((os.path.join(dst_directory, dst_subdirectory), [full_path]))
        elif os.path.isdir(curdir(full_path)):
            paths.extend(all_files_in(dst_directory, full_path))    
            
    return paths

def all_subpackages_in(package):
    'Returns all subpackages (packages in subdirectories) (recursive)'
    subpackages = []
    
    for filename in os.listdir(curdir(package)):
        print 'FN: ', filename
        if filename in EXCLUDE_FILES:
            continue
        full_path = os.path.join(package, filename)
        print 'isdir(%s, %s)' % (full_path, os.path.isdir(curdir(full_path)))
        if os.path.isdir(curdir(full_path)):
            print 'PAC: ', filename
            subpackages.append(full_path.replace('/', '.'))
            subpackages.extend(all_subpackages_in(full_path))
    print "SUBPACKAGES: ", subpackages
    return subpackages
            
             
    

def main():
    setup(name = PACKAGE_NAME,
          description = 'Admin Interface for FRED (Fast Registry for Enum and Domains)',
          author = 'David Pospisilik, Tomas Divis, CZ.NIC',
          author_email = 'tdivis@nic.cz',
          url = 'http://www.nic.cz',
          version = PACKAGE_VERSION,
          packages = [PACKAGE_NAME] + all_subpackages_in(PACKAGE_NAME),
          package_dir = {PACKAGE_NAME: PACKAGE_NAME},
#          scripts = ['fred-webadmin'],
          data_files = [
#                        (CONFIG_DIR, ['webadmin_cfg.py']),
#                        (BIN_DIR, ['fred-webadmin']),
                        (SHARE_DOC, [curdir('doc/INSTALL.txt')]),
#                        ('/var/lib/fred_webadmin/sessions', [])
                       ] +
                       all_files_in(SHARE_WWW, 'www') +
                       all_files_in(SHARE_LOCALE, 'locale'),
          cmdclass = {'build': FredWebAdminBuild,
                      'build_py': FredWebAdminBuildPy,
                      'install': FredWebAdminInstall,
                      'install_data': FredWebAdminInstallData
                     },
    )
    return True

    
if __name__ == '__main__':
    g_srcdir = os.path.dirname(sys.argv[0])
    if not g_srcdir:
        g_srcdir = os.curdir
    if main():
        print "All done!"
