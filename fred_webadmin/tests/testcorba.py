#!/usr/bin/env python
#
# Copyright (C) 2008-2018  CZ.NIC, z. s. p. o.
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

if __name__ == '__main__':
    from IPython import embed
    from omniORB.any import from_any

    from fred_webadmin.corba import Corba, ccReg, Registry
    from fred_webadmin.corbarecoder import CorbaRecode

    recoder = CorbaRecode('utf-8')
    c2u = recoder.decode  # recode from corba string to unicode
    u2c = recoder.encode  # recode from unicode to strings

    corba = Corba()
    corba.connect('pokuston:50001', 'fred')

    a = corba.getObject('Admin', 'ccReg.Admin')
    s = a.getSession(a.createSession('helpdesk'))
    embed()  # 'Use "a" as Admin or "s" as Session'
