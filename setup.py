from distutils.core import setup
from distutils.command.build_py import build_py
from distutils.command.install import install
from distutils.command.install_data import install_data
import os

PACKAGE_NAME = 'fred_webadmin'
PACKAGE_VERSION = '1.0'

SHARE_DOC = os.path.join('share', 'doc', PACKAGE_NAME)
SHARE_PACKAGE = os.path.join('share', PACKAGE_NAME)
SHARE_WWW = os.path.join(SHARE_PACKAGE, 'www')
SHARE_LOCALE = os.path.join(SHARE_PACKAGE, 'locale')


class FredWebAdminBuild(build_py):
    pass
#    def run(self):
#        #import pdb; pdb.set_trace()
#        self.ensure_finalized()
#        print "BEGIN RUN "
#        print self.data_files
#        print "END RUN "


class FredWebAdminInstall(install):
    pass

class FredWebAdminData(install_data):
    pass    

def all_files_in(dir):
    'Returns paths to all files in dir (recursive)'
    paths = []

    for filename in os.listdir(dir):
        full_path = os.path.join(dir, filename)
        if os.path.isfile(full_path): 
            paths.append(full_path)
        elif os.path.isdir(full_path):
            paths.extend(all_files_in(full_path))                   
            
    return paths


if __name__ == '__main__':
    setup(name = PACKAGE_NAME,
          description = 'Admin Interface for FRED (Fast Registry for Enum and Domains)',
          author = 'David Pospisilik, Tomas Divis, CZ.NIC',
          author_email = 'tdivis@nic.cz',
          url = 'http://www.nic.cz',
          version = PACKAGE_VERSION,
          packages = [PACKAGE_NAME],
          package_dir = {PACKAGE_NAME: PACKAGE_NAME
                         
                        },
          
          data_files = [('/etc/fred/webadmin_cfg.py.example', ['webadmin_cfg.py.example']),
                        (SHARE_DOC, all_files_in('doc')),
                        (SHARE_WWW, all_files_in('www')),
                        (SHARE_LOCALE, all_files_in('locale')),
                        ('/tmp/fred_webadmin_session', [])
                       ],
          cmdclass = {'build_py': FredWebAdminBuild,
                      'install': FredWebAdminInstall, 
                      'install_data': FredWebAdminData
                     },
    )
    
