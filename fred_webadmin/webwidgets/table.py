from fred_webadmin.webwidgets.gpyweb.gpyweb import noesc, attr, table, thead, tbody, tfoot, tr, th, td, a, img, span, br, form, input, div
from fred_webadmin.translation import _

class WIterTable(table):
    def __init__(self, itertable, *content, **kwd):
        self.media_files=['/js/logging.js', 
                          '/js/itertable.js',
                          '/css/itertable.css']
        super(WIterTable, self).__init__(*content, **kwd)
        self.tag = 'table'
        self.column_count = len(itertable.header)
        
        header = tr(attr(cssc="wi_header"))
        for htext in itertable.header:            
            header.add(th(htext))
        self.add(thead(header))
        
        rows = []
        for irow in itertable:
            row = tr()
            for col in irow:
                if col.get('icon'):
                    val = img(attr(src=col['icon']))
                else:
                    val = col['value']
                
                if col.get('url'):
                    val = a(attr(href=col['url']), val)
                
                row.add(td(attr(cssc=col.get('cssc')), val))
            rows.append(row)
        self.add(tbody(rows))
        
        
        # Pager
        pager = span()

        # Numbers of entries 
        if itertable.total_rows > itertable.num_rows:
            num_rows = span(attr(cssc='warning'), itertable.num_rows)
        else:
            num_rows = itertable.num_rows
        
        pager.add(div(attr(style='float: right'),
            '%s: %s,' % (_('Number_of_pages'), itertable.last_page),
            '%s: ' % _('entries'), num_rows, ',', 
            '%s: %s' % (_('total'), itertable.total_rows),
            #br()
        ))
        
        if itertable.num_pages > 1:
            pager.add(
                a(attr(cssc='pager-button', href='?page=%s' % itertable.first_page), noesc('&laquo;')),
                a(attr(cssc='pager-button', href='?page=%s' % itertable.prev_page), noesc('&lsaquo;')),
#                    a(attr(cssc='pager-button', href='?page=%s' % itertable._number), itertable._number),
                form(attr(style='display: inline;', method='GET'), input(attr(type='text', size='2', name='page', value=itertable.current_page))),
                a(attr(cssc='pager-button', href='?page=%s' % itertable.next_page), noesc('&rsaquo;')),
                a(attr(cssc='pager-button', href='?page=%s' % itertable.last_page), noesc('&raquo;'))
            )
        self.add(tfoot(tr(td(attr(colspan=self.column_count), pager))))
        