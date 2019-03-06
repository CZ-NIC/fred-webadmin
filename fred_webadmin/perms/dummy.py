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

class Authorizer(object):
    """ Implements the authorizer interface and allows every action.
        To be used when permission checking is disabled.
    """
    def __init__(self, username):
        self._username = username

    def has_permission(self, obj, action):
        return True

    def has_permission_detailed(self, obj, action, obj_id):
        return True

    def check_detailed_present(self, obj, action):
        return False

    def has_field_permission(self, obj, action, field_name):
        return True
