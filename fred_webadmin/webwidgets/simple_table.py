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

from fred_webadmin.webwidgets.gpyweb.gpyweb import (attr, table, thead, tbody, tfoot, tr, th, td,)


class SimpleTable(table):
    ''' Simple HTML table widget '''
    def __init__(self, header, data, footer=None, *content, **kwd):
        super(SimpleTable, self).__init__(*content, **kwd)
        self.header = header
        self.data = data
        self.footer = footer
        self.tag = 'table'

    def render(self, indent_level=0):
        if self.header:
            self.add(thead(tr([th(item) for item in self.header])))

        if self.data:
            rows = []
            for row_num, data_row in enumerate(self.data):
                row = tr(attr(cssc='row%s' % ((row_num % 2) + 1)))
                for col in data_row:
                    row.add(td(col))
                rows.append(row)
            self.add(tbody(rows))

        if self.footer:
            self.add(tfoot([th(item) for item in self.footer]))
        return super(SimpleTable, self).render(indent_level)
