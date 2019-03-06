#
# Copyright (C) 2010-2018  CZ.NIC, z. s. p. o.
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

import ldap
import fred_webadmin.controller.adiferrors
from fred_webadmin import config
from fred_webadmin.translation import _


def authenticate_user(admin, username=None, password=None):  # pylint: disable=W0613
    """ Authenticate user using LDAP server.
    """
    try:
        l = ldap.initialize(config.LDAP_server)
        l.simple_bind_s(config.LDAP_scope % username, password)
    except ldap.SERVER_DOWN:
        raise fred_webadmin.controller.adiferrors.AuthenticationError(_('LDAP server is unavailable!'))
    except ldap.INVALID_CREDENTIALS:
        raise fred_webadmin.controller.adiferrors.AuthenticationError(_('Invalid username and/or password!'))
