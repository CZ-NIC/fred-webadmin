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

from fred_webadmin.translation import _
from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget, tagid, attr, div, table, tbody, tr, td, input, fieldset


class FormSetLayout(WebWidget):
    pass


class TableFormSetLayout(FormSetLayout):
    columns_count = 1
    tattr_list = table.tattr_list

    def __init__(self, formset, *content, **kwd):
        super(TableFormSetLayout, self).__init__(*content, **kwd)

        self.tag = u'table'
        self.cssc = 'form_table formset_table'
        self.formset = formset
        self.create_layout()

    def create_layout(self):
        self.content = []
        formset = self.formset

        self.add(tbody(tagid('tbody')))

        if formset.non_form_errors():
            self.tbody.add(tr(td(
                attr(colspan=self.columns_count),
                _('Errors:'), formset.non_form_errors())))

        for form in formset.forms:
            self.tbody.add(tr(td(form)))

        formset.add(formset.management_form.fields.values())
        if not formset.is_nested:
            self.tbody.add(self.get_submit_row())

    def get_submit_row(self):
        return tr(td(
            attr(colspan=self.columns_count, cssc='center'),
            input(attr(type=u'submit', value=u'Save set', name=u'submit'))))


class DivFormSetLayout(FormSetLayout):
    columns_count = 1
    tattr_list = table.tattr_list

    def __init__(self, formset, *content, **kwd):
        super(TableFormSetLayout, self).__init__(*content, **kwd)

        self.tag = u'div'
#        self.cssc = 'form_table formset_table'
        self.formset = formset
        self.create_layout()

    def create_layout(self):
        self.content = []
        formset = self.formset

        self.add(div(tagid('div')))

        if formset.non_form_errors():
            self.div.add(div(_('Errors:')), div(formset.non_form_errors()))

        for form in formset.forms:
            self.div.add(div(form))

        formset.add(formset.management_form.fields.values())
        if not formset.is_nested:
            self.div.add(self.get_submit_row())

    def get_submit_row(self):
        return div(input(attr(type=u'submit', value=u'Save set', name=u'submit')))


class FieldsetFormSetLayout(TableFormSetLayout):
    def create_layout(self):
        self.content = []
        formset = self.formset

        self.add(fieldset(tagid('fieldset')))
        self.fieldset.add(tbody(tagid('tbody')))
        tb = self.fieldset.tbody

        if formset.non_form_errors():
            tb.add(tr(td(
                attr(colspan=self.columns_count),
                _('Errors:'), formset.non_form_errors())))

        for form in formset.forms:
            tb.add(tr(td(form)))

        formset.add(formset.management_form.fields.values())
        if not formset.is_nested:
            tb.add(self.get_submit_row())
