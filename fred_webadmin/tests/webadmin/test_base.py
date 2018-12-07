#
# Copyright (C) 2014-2018  CZ.NIC, z. s. p. o.
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

from .base import enable_corba_comparison, revert_to_default_corba_comparison, enable_corba_comparison_decorator
from fred_webadmin.corba import Registry, ccReg


class TestCorbaComparison(object):
    def test_corba_comaprison_not_working(self):
        assert ccReg.DateType(1, 1, 2000) != ccReg.DateType(1, 1, 2000)

    def test_corba_enabling_comparison(self):
        assert ccReg.DateType(1, 1, 2000) != ccReg.DateType(1, 1, 2000)
        enable_corba_comparison(ccReg.DateType)
        assert ccReg.DateType(1, 1, 2000) == ccReg.DateType(1, 1, 2000)
        assert ccReg.DateType(1, 1, 2000) != ccReg.DateType(2, 1, 2000)
        revert_to_default_corba_comparison(ccReg.DateType)
        assert ccReg.DateType(1, 1, 2000) != ccReg.DateType(1, 1, 2000)

    @enable_corba_comparison_decorator(ccReg.DateType)
    def test_corba_comaprison_decorator(self):
        assert ccReg.DateType(1, 1, 2000) == ccReg.DateType(1, 1, 2000)
