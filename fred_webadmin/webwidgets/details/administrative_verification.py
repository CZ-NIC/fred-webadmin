import cherrypy

from fred_webadmin.enums import ContactCheckEnums as enums
from fred_webadmin.webwidgets.gpyweb.gpyweb import (attr, table, form, thead, tbody, tfoot, tr, th, td,
                                                    input, span, strong, em, br)
from fred_webadmin.translation import _


class VerificationCheckDetail(form):
    ''' Simple HTML table widget '''

    def __init__(self, check, resolve, form=None, *content, **kwd):
        super(VerificationCheckDetail, self).__init__(*content, **kwd)
        self.tag = 'form'
        self.header = [_('Test'), _('Tested data'), _('Updated'), _('Processed by'), _('Error'), _('Status'), _('Change to')]
        self.check = check
        self.form = form
        self.method = 'post'

        self.resolve = resolve
        if not resolve:
            self.header.pop()  # remove last column which contains form fields for resolving the check

    def _render_status(self, test_row, status):
        test_row.add(td(attr(cssc='no-wrap'), status.update))

        if status.logd_request_id:
            # TODO: Get user from detail of log request or myabe display ling to log req.
            test_row.add(td('A good guy', status.logd_request_id))
        else:
            test_row.add(td(_('automat')))
        test_row.add(td(status.err_msg))
        test_row.add(td(attr(title=enums.TEST_STATUS_DESCS[status.status]), enums.TEST_STATUS_NAMES[status.status]))

    def render(self, indent_level=0):
        col_count = len(self.header)

        tests_table = table()
        self.add(tests_table)
        tests_table.media_files.append('/css/details.css')
        tests_table.add_css_class('section_table')
        if cherrypy.session.get('history', False):
            tests_table.add_css_class('history')

        tests_table.add(thead([th(item) for item in self.header]))

        if self.check.test_list:
            for row_num, test_data in enumerate(sorted(self.check.test_list,
                                                       key=lambda k: enums.TEST_DESCS[k.test_handle])):
                rows = []
                row = tr(attr(cssc='row%s' % ((row_num % 2) + 1)))
                row.add(td(attr(title=enums.TEST_DESCS[test_data.test_handle]),
                           enums.TEST_NAMES[test_data.test_handle]))

                tested_data_td = td(test_data.tested_contact_data)
                if test_data.current_contact_data != test_data.tested_contact_data:
                    tested_data_td.add([br(), em(_('Changed to:')), strong(test_data.current_contact_data)])

                row.add(tested_data_td)

                current_status = test_data.status_history[-1]
                self._render_status(row, current_status)

                if self.resolve:
                    row.add(td(self.form.fields[test_data.test_handle]))

                rows.append(row)

                if cherrypy.session.get('history', False):
                    for older_status in reversed(test_data.status_history[0:-1]):
                        row = tr(attr(cssc='row%s' % ((row_num % 2) + 1)))
                        row.add(td(attr(colspan=2, cssc='borderless')))
                        self._render_status(row, older_status)
                        rows.append(row)

                # one tbody per test - tbodies have double border in css to separate tests as sections:
                tests_table.add(tbody(rows))

            if self.resolve:
                tests_table.add(tbody(tr(td(attr(colspan=col_count - 1)),
                                         td(input(attr(type='submit', value=self.form.submit_button_text))))))

        tests_table.add(tfoot(th(attr(colspan=col_count - 1), _('Overall status:'),
                                td(span(attr(title=enums.CHECK_STATUS_DESCS[self.check.status_history[-1].status]),
                                        enums.CHECK_STATUS_NAMES[self.check.status_history[-1].status]))
                                if self.check.status_history else _('No status'))
                       ))

        return super(VerificationCheckDetail, self).render(indent_level)
