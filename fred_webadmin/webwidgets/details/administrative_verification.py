import cherrypy

from fred_webadmin.enums import ContactCheckEnums as enums, get_status_action
from fred_webadmin.webwidgets.gpyweb.gpyweb import (attr, save, form, button, span, br, div,
                                                    table, caption, thead, tbody, tfoot, tr, th, td)
from fred_webadmin.translation import _
from fred_webadmin.webwidgets.adifwidgets import FilterPanel


class VerificationCheckDetail(div):
    ''' Simple HTML table widget '''

    def __init__(self, check, resolve, form=None, *content, **kwd):
        super(VerificationCheckDetail, self).__init__(*content, **kwd)
        self.tag = 'div'
        self.header = [_('Test'), _('Tested data'), _('Error'), _('Status'), _('Processed by'), _('Updated')]
        self.check = check
        self.form = form

        self.resolve = resolve

    def _render_status(self, test_row, status, test_handle, is_current_status):
        test_row.add(td(status.err_msg))
        status_td = td(attr(cssc='no-wrap status_col'))

        if is_current_status and self.resolve:
            status_td.add(self.form.fields[test_handle])
        else:
            status_td.add(span(attr(title=enums.TEST_STATUS_DESCS[status.status]),
                               enums.TEST_STATUS_NAMES[status.status]))
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

    def _format_tested_data(self, tested_data):
        return br().join([item for item in tested_data if item])

    def render(self, indent_level=0):
        col_count = len(self.header)

        tests_table = table(attr(cssc='verification_check_table'),
                            caption(attr(cssc='section_label'), _('Tests:')))

        if self.resolve:
            self.add(form(attr(method='post', onsubmit='return confirm("%s")' % _('Are you sure?')),
                          tests_table))
        else:
            self.add(tests_table)

        tests_table.media_files.extend(['/css/details.css', '/js/contactcheck_detail.js'])
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

                current_status = test_data.status_history[-1]
                if current_status.status == 'ok':
                    row.add_css_class('status_ok')
                elif current_status.status == 'fail':
                    row.add_css_class('status_fail')

                row.add(td(attr(title=enums.TEST_DESCS[test_data.test_handle]),
                           enums.TEST_NAMES[test_data.test_handle]))

                row.add(td(self._format_tested_data(test_data.tested_contact_data)))
                if tested_data_changed:
                    if test_data.current_contact_data != test_data.tested_contact_data:
                        row.add(td(self._format_tested_data(test_data.current_contact_data)))
                    else:
                        row.add(td())

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

        current_check_status = self.check.status_history[-1].status
        tests_table.add(tfoot(save(tests_table, 'footer'),
                              tr(save(tests_table, 'footer_th'),
                                 th(attr(colspan=col_count), _('Overall status:'),
                                    span(attr(title=enums.CHECK_STATUS_DESCS[current_check_status]),
                                         enums.CHECK_STATUS_NAMES[current_check_status])
                                    if self.check.status_history else _('No status')))
                       ))
        if current_check_status == 'ok':
            tests_table.footer_th.add_css_class('status_ok')
        elif current_check_status == 'fail':
            tests_table.footer_th.add_css_class('status_fail')

        if self.resolve:

            tests_table.footer.add(tr(td(attr(colspan=col_count),
                table(attr(cssc='submit-row'),
                      tr(td(button(attr(type='submit', name='status_action', value=status_action), action_name))
                         for status_action, action_name in get_status_action(self.check.test_suite_handle, current_check_status).items()

                      ))
            )))

        filters = [[[_('Domains_owner'), 'domain', [{'Registrant.Handle': self.check.contact_handle}]]]]
        panel = FilterPanel(filters)
        self.add(panel)

        return super(VerificationCheckDetail, self).render(indent_level)
