#!/usr/bin/python
# -*- coding: utf-8 -*-
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

import gettext
import config


####################################
# gettext
####################################

translate = gettext.translation(config.gettext_domain, config.localepath, languages=[config.lang]).ugettext

_ = translate

#def _(key, encoding='utf-8'):
#   return translate(key).decode(encoding)
#   #return translate(key)#.decode(encoding)

####################################
