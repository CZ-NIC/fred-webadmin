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
