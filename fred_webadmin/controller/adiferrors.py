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

class AdifError(Exception):
    def __init__(self, msg):
        self.msg = msg.encode("utf-8")

    def __str__(self):
        return self.msg


class PermissionDeniedError(AdifError):
    pass


class IorNotFoundError(AdifError):
    pass


class AuthenticationError(AdifError):
    pass


class AuthorizationError(AdifError):
    pass


class MalformedAuthorizationError(AuthorizationError):
    pass
