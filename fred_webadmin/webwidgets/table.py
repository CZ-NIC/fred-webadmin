import urlparse

from fred_webadmin.webwidgets.gpyweb.gpyweb import noesc, attr, table, thead, tbody, tfoot, tr, th, td, a, img, span, br, form, input, div
from fred_webadmin.translation import _
from fred_webadmin.utils import get_current_url, append_getpar_to_url


class WIterTable(table):
    def __init__(self, itertable, *content, **kwd):
        super(WIterTable, self).__init__(*content, **kwd)
        self.media_files = ['/js/logging.js', 
                            '/css/itertable.css',
                           ]
        
        self.tag = 'table'
        self.cssc = 'itertable'
        self.column_count = len(itertable.header)
        
        sort_col_num, sort_direction = itertable.get_sort()
        
        header = tr(attr(cssc="wi_header"))

        for i, htext in enumerate(itertable.header):
            col_num = i - 1
            if col_num == -1: # first column is ID
                header.add(th(htext))
            else:
                sort_dir = 1
                if col_num == sort_col_num and sort_direction: # rendering column, according which is table sorted, so reverse direction for next click on this column 
                    sort_dir = 0
                th_cell = th(a(attr(href=append_getpar_to_url(add_par_dict={'sort_col': col_num, 'sort_dir': sort_dir}, del_par_list=['load', 'show_form'])), htext))
                if col_num == sort_col_num:
                    th_cell.cssc = 'sorted ' + ['ascending', 'descending'][sort_direction]
                header.add(th_cell)
        self.add(thead(header))
        
        rows = []
        for row_num, irow in enumerate(itertable):
            row = tr(attr(cssc='row%s' % ((row_num % 2) + 1)))
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
        #if itertable.total_rows > itertable.num_rows:
        if itertable.num_rows_over_limit:
            num_rows = span(attr(cssc='warning'), itertable.num_rows)
        else:
            num_rows = itertable.num_rows
        
        pager.add(span(attr(cssc='pager_text'),
            noesc('Displaying results %s - %s of %s' % (itertable.page_start, itertable.page_start + itertable.page_rows, num_rows))
#            '%s: %s,' % (_('Number_of_pages'), itertable.last_page),
#            '%s: ' % _('entries'), num_rows, ',', 
#            '%s: %s' % (_('total'), itertable.total_rows),
#            #br()
        ))
        
        if itertable.num_pages > 1:
#            pager.add(
#                a(attr(cssc='pager-button', href='?page=%s' % itertable.first_page), noesc('&laquo;')),
#                a(attr(cssc='pager-button', href='?page=%s' % itertable.prev_page), noesc('&lsaquo;')),
##                    a(attr(cssc='pager-button', href='?page=%s' % itertable._number), itertable._number),
#                form(attr(style='display: inline;', method='GET'), input(attr(type='text', size='2', name='page', value=itertable.current_page))),
#                a(attr(cssc='pager-button', href='?page=%s' % itertable.next_page), noesc('&rsaquo;')),
#                a(attr(cssc='pager-button', href='?page=%s' % itertable.last_page), noesc('&raquo;'))
#            )
            if itertable.current_page == 1:
                first_button = span(attr(cssc='pager-button'), img(attr(src='/css/ext/images/default/grid/page-first-disabled.gif')))
                prev_button = span(attr(cssc='pager-button'), img(attr(src='/css/ext/images/default/grid/page-prev-disabled.gif'))), 
            else:
                first_button = a(attr(cssc='pager-button', href='?page=%s' % itertable.first_page), img(attr(src='/css/ext/images/default/grid/page-first.gif'))),
                prev_button = a(attr(cssc='pager-button', href='?page=%s' % itertable.prev_page), img(attr(src='/css/ext/images/default/grid/page-prev.gif'))),
            if itertable.current_page == itertable.last_page:
                next_button = span(attr(cssc='pager-button'), img(attr(src='/css/ext/images/default/grid/page-next-disabled.gif'))),
                last_button = span(attr(cssc='pager-button'), img(attr(src='/css/ext/images/default/grid/page-last-disabled.gif'))) 
            else:
                next_button = a(attr(cssc='pager-button', href='?page=%s' % itertable.next_page), img(attr(src='/css/ext/images/default/grid/page-next.gif'))),
                last_button = a(attr(cssc='pager-button', href='?page=%s' % itertable.last_page), img(attr(src='/css/ext/images/default/grid/page-last.gif'))) 
                
            pager.add(
                first_button,
                prev_button,
#                    a(attr(cssc='pager-button', href='?page=%s' % itertable._number), itertable._number),
                form(attr(style='display: inline;', method='GET'), input(attr(type='text', size='2', name='page', value=itertable.current_page)), ' of %d ' % itertable.last_page),
                next_button,
                last_button
            )
        self.add(tfoot(tr(td(attr(colspan=self.column_count), pager))))
        