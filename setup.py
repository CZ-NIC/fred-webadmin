import os

from freddist.core import setup
from freddist.command.install import install
from freddist.util import find_packages, find_data_files


PROJECT_NAME = 'fred-webadmin'

DEFAULT_NSCONTEXT = 'fred'
DEFAULT_NSHOST = 'localhost'
DEFAULT_NSPORT = '2809'
DEFAULT_WEBADMINPORT = '18456'


class FredWebAdminInstall(install):
    user_options = install.user_options + [
        ('nscontext=', None, 'CORBA nameservice context name [fred]'),
        ('nshost=', None, 'CORBA nameservice host [localhost]'),
        ('nsport=', None, 'Port where CORBA nameservice listen [2809]'),
        ('webadminport=', None, 'Port of fred-webadmin  [18456]'),
        ('ldapserver=', None, 'LDAP server'),
        ('ldapscope=', None, 'LDAP scope'),
        ("idldir=", "d", "directory where IDL files reside [PREFIX/share/idl/fred]"),
    ]

    DEPS_PYMODULE = ('simplejson', 'omniORB.CORBA', 'dns', 'cherrypy (>= 3.0.0)', 'cherrypy (<= 4.0.0)')

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

    def finalize_options(self):
        install.finalize_options(self)
        if not self.idldir:
            self.idldir = self.expand_filename('$data/share/idl/fred')

        if self.ldapserver and self.ldapscope:
            self.authentization = 'LDAP'
        else:
            self.authentization = 'CORBA'

    def update_config_py(self, filename):
        content = open(filename).read()
        content = content.replace("sys.path.insert(0, '/etc/fred/')",
                                  "sys.path.insert(0, '%s')" % self.expand_filename('$sysconf/fred'))
        open(filename, 'w').write(content)
        self.announce("File '%s' was updated" % filename)

    def update_webadmin_cfg(self, filename):
        content = open(filename).read()
        content = content.replace('DU_IDL_DIR', os.path.normpath(self.idldir))
        content = content.replace('DU_DATAROOTDIR', self.expand_filename('$data/share'))
        content = content.replace('DU_LOCALSTATEDIR', self.expand_filename('$localstate'))
        content = content.replace('DU_SYSCONFDIR', self.expand_filename('$sysconf'))
        content = content.replace('DU_LOCALE_DIR', self.expand_filename('$purelib/fred_webadmin/locale'))
        content = content.replace('DU_NS_HOST', '%s:%s' % (self.nshost, self.nsport))
        content = content.replace('DU_NS_CONTEXT', self.nscontext)
        content = content.replace('DU_WEBADMIN_PORT', self.webadminport)
        content = content.replace('DU_AUTHENTICATION', self.authentization)
        content = content.replace('DU_LDAP_SERVER', self.ldapserver)
        content = content.replace('DU_LDAP_SCOPE', self.ldapscope)
        open(filename, 'w').write(content)
        self.announce("File '%s' was updated" % filename)

    def update_fred_webadmin(self, filename):
        content = open(filename).read()
        paths = [self.expand_filename('$sysconf/fred'), self.expand_filename('$purelib')]
        content = content.replace('DU_PYTHON_PATHS', str(paths))
        open(filename, 'w').write(content)
        self.announce("File '%s' was updated" % filename)

    def update_webadmin_server(self, filename):
        content = open(filename).read()
        content = content.replace('DU_WEBADMIN_BIN', self.expand_filename('$scripts/fred-webadmin'))
        content = content.replace('DU_LOCALSTATEDIR', self.expand_filename('$localstate'))
        open(filename, 'w').write(content)
        self.announce("File '%s' was updated" % filename)


def main():
    srcdir = os.path.dirname(os.path.abspath(__file__))

    packages = find_packages(srcdir)
    data_files = [
        ('$localstate/log/fred-webadmin', []),
        ('$localstate/lib/%s/sessions' % PROJECT_NAME, []),
        ('$sysconf/init.d', ['fred-webadmin-server']),
        ('$sysconf/fred', ['webadmin_cfg.py'])] + \
        [(os.path.join('share/%s/www' % PROJECT_NAME, dest), files)
         for dest, files in find_data_files(srcdir, 'www')]

    setup(name=PROJECT_NAME,
          description='Admin Interface for FRED (Fast Registry for Enum and Domains)',
          author='David Pospisilik, Tomas Divis, CZ.NIC',
          author_email='tdivis@nic.cz',
          url='http://www.nic.cz',
          packages=packages,
          scripts=['fred-webadmin'],
          i18n_files=['fred_webadmin/locale/cs_CZ/LC_MESSAGES/adif.po',
                      'fred_webadmin/locale/en_US/LC_MESSAGES/adif.po'],
          data_files=data_files,
          modify_files={'$purelib/fred_webadmin/config.py': 'update_config_py',
                        '$sysconf/fred/webadmin_cfg.py': 'update_webadmin_cfg',
                        '$scripts/fred-webadmin': 'update_fred_webadmin',
                        '$sysconf/init.d/fred-webadmin-server': 'update_webadmin_server'},
          cmdclass={'install': FredWebAdminInstall})


if __name__ == '__main__':
    main()
