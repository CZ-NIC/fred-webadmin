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

import types

from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget
from fred_webadmin.webwidgets.utils import pretty_name


class AbstractDetailLayout(WebWidget):
    ''' Common parent class for DetailLayouts and SectionLayouts (look at SectionDetailLayout)'''
    def __init__(self, detail, *content, **kwd):
        super(AbstractDetailLayout, self).__init__(*content, **kwd)
        self.detail = detail

    def get_label_name(self, field_or_string):
        if isinstance(field_or_string, types.StringTypes):
            label_str = field_or_string
        else:
            label_str = field_or_string.label

        if label_str == '':  # if empty string is explicitly specified, it really should return empty string
            return ''

        if not label_str:
            label_str = pretty_name(field_or_string.name)
        if self.detail.label_suffix and label_str[-1] not in ':?.!':
            label_str += self.detail.label_suffix
        return label_str
