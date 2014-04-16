import cherrypy

from fred_webadmin.enums import ContactCheckEnums as enums
from fred_webadmin.webwidgets.gpyweb.gpyweb import (attr, table, form, thead, tbody, tfoot, tr, th, td, input, span)
from fred_webadmin.translation import _
from fred_webadmin.webwidgets.adifwidgets import FilterPanel


class VerificationCheckDetail(form):
    ''' Simple HTML table widget '''

    def __init__(self, check, resolve, form=None, *content, **kwd):
        super(VerificationCheckDetail, self).__init__(*content, **kwd)
        self.tag = 'form'
        self.onsubmit = 'return confirm("%s")' % _('Are you sure?')
        self.header = [_('Test'), _('Tested data'), _('Error'), _('Status'), _('Processed by'), _('Updated')]
        self.check = check
        self.form = form
        self.method = 'post'

        self.resolve = resolve

    def _render_status(self, test_row, status, test_handle, is_current_status):
        test_row.add(td(status.err_msg))
        status_td = td(attr(cssc='no-wrap', style='text-align: right;'),
                       span(attr(title=enums.TEST_STATUS_DESCS[status.status]), enums.TEST_STATUS_NAMES[status.status]))

        if is_current_status and self.resolve:
            status_td.add(self.form.fields[test_handle])
        test_row.add(status_td)

        if status.logd_request_id:
            # TODO: Get user from detail of log request or myabe display link to log req.
            test_row.add(td('A good guy', status.logd_request_id))
        else:
            test_row.add(td(_('automat')))

        test_row.add(td(attr(cssc='no-wrap'), status.update))

    def get_data_info(self):
        ''' In one cycle, get info that:
             * any test contains changed contact data
        '''
        tested_data_changed = False
        for test_data in self.check.test_list:
            if test_data.current_contact_data != test_data.tested_contact_data:
                tested_data_changed = True

        return tested_data_changed

    def render(self, indent_level=0):
        col_count = len(self.header)

        tests_table = table()
        self.add(tests_table)
        tests_table.media_files.append('/css/details.css')
        tests_table.add_css_class('section_table')
        if cherrypy.session.get('history', False):
            tests_table.add_css_class('history')

        tested_data_changed = self.get_data_info()
        if tested_data_changed:
            self.header.insert(self.header.index(_('Tested data')) + 1, _('Changed to'))

        tests_table.add(thead([th(item) for item in self.header]))

        if self.check.test_list:
            for row_num, test_data in enumerate(sorted(self.check.test_list,
                                                       key=lambda k: enums.TEST_DESCS[k.test_handle])):
                rows = []
                row = tr(attr(cssc='row%s' % ((row_num % 2) + 1)))
                row.add(td(attr(title=enums.TEST_DESCS[test_data.test_handle]),
                           enums.TEST_NAMES[test_data.test_handle]))

                row.add(td(test_data.tested_contact_data))
                if tested_data_changed:
                    if test_data.current_contact_data != test_data.tested_contact_data:
                        row.add(td(test_data.current_contact_data))
                    else:
                        row.add(td())

                current_status = test_data.status_history[-1]
                self._render_status(row, current_status, test_data.test_handle, True)

                rows.append(row)

                if cherrypy.session.get('history', False):
                    for older_status in reversed(test_data.status_history[0:-1]):
                        row = tr(attr(cssc='row%s' % ((row_num % 2) + 1)))
                        row.add(td(attr(colspan=3 if tested_data_changed else 2, cssc='borderless')))
                        self._render_status(row, older_status, test_data.test_handle, False)
                        rows.append(row)

                # one tbody per test - tbodies have double border in css to separate tests as sections:
                tests_table.add(tbody(rows))

#             if self.resolve:
#                 tests_table.add(tbody(tr(td(attr(colspan=col_count - 1)),
#                                          td())))

        tests_table.add(tfoot(th(attr(colspan=col_count - 1), _('Overall status:'),
                                td(span(attr(title=enums.CHECK_STATUS_DESCS[self.check.status_history[-1].status]),
                                        enums.CHECK_STATUS_NAMES[self.check.status_history[-1].status]))
                                if self.check.status_history else _('No status'))
                       ))

        if self.resolve:
            filters = [[
                [input(attr(type='submit', name='submit_fail', value=_('Resolve as failed')))],
                [input(attr(type='submit', name='submit_invalidate', value=_('Invalidate')))],
                [input(attr(type='submit', name='submit_ok', value=_('Resolve as OK')))],
            ]]
            panel = FilterPanel(filters)
            panel.media_files.append('/js/public_profile.js')
            self.add(panel)

        return super(VerificationCheckDetail, self).render(indent_level)
