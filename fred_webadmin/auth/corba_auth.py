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

import fred_webadmin.corbarecoder as recoder
import fred_webadmin.controller.adiferrors
from fred_webadmin.corba import ccReg
from fred_webadmin.translation import _


def authenticate_user(admin, username=None, password=None):
    """ Authenticate user using CORBA backend.
    """
    try:
        admin.authenticateUser(recoder.u2c(username), recoder.u2c(password))
    except ccReg.Admin.AuthFailed:
        raise fred_webadmin.controller.adiferrors.AuthenticationError(
            _('Invalid username and/or password!'))
