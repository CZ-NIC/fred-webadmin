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

from distutils.command.build import build

from setuptools import find_packages, setup
from setuptools.command.sdist import sdist


class custom_build(build):

    sub_commands = [('compile_catalog', lambda x: True)] + build.sub_commands


class custom_sdist(sdist):

    def run(self):
        self.run_command('compile_catalog')
        # sdist is an old style class so super cannot be used.
        sdist.run(self)


setup(name='fred-webadmin',
      description='Admin Interface for FRED',
      version='3.25.3',
      author='David Pospisilik, Tomas Divis, CZ.NIC',
      author_email='podpora@nic.cz',
      url='http://fred.nic.cz/',
      license='GNU GPL v3.0',
      platforms=['posix'],
      long_description='Admin Interface for FRED (Fast Registry for Enum and Domains)',
      packages=find_packages(),
      include_package_data=True,
      scripts=['fred-webadmin'],
      setup_requires=['Babel >=2.3'],
      install_requires=['cherrypy', 'simplejson', 'fred-pylogger'],
      extras_require={'ldap': ['python-ldap'],
                      'prettyprint': ['python-xml', 'pygments']},
      dependency_links=open('dependency_links.txt').read().splitlines(),
      cmdclass={'build': custom_build, 'sdist': custom_sdist})
