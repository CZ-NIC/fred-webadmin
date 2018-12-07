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

from fred_webadmin.translation import _
from fred_webadmin.webwidgets.gpyweb.gpyweb import (
    WebWidget, tagid, attr, div, table, tbody, tr, th, td,
    input, label, a, legend)
from fred_webadmin.webwidgets.utils import pretty_name


class FormLayout(WebWidget):
    def __init__(self, form, *content, **kwd):
        self.form = form
        super(FormLayout, self).__init__(*content, **kwd)


class TableFormLayout(FormLayout):
    columns_count = 2
    tattr_list = table.tattr_list

    def __init__(self, form, *content, **kwd):
        super(TableFormLayout, self).__init__(form, *content, **kwd)
        self.tag = u'table'
        self.cssc = u'form_table'
        self.create_layout()

    def create_layout(self):
        self.content = []
        form = self.form
        self.add(tbody(tagid('tbody')))

        if form.non_field_errors():
            self.tbody.add(tr(td(attr(colspan=self.columns_count), _('Errors:'), form.non_field_errors())))
        hidden_fields = []
        for field in form.fields.values():
            if field.is_hidden:
                hidden_fields.append(field)
                continue

            label_str = self.get_label_name(field)

            if field.required:
                cell_tag = th
            else:
                cell_tag = td

            errors = form.errors.get(field.name_orig, None)

            self.tbody.add(tr(
                cell_tag(attr(cssc='label_cell'), label(label_str)),
                td(errors, field)))
        self.add(hidden_fields)

        if not form.is_nested:
            self.tbody.add(self.get_submit_row())

    def get_label_name(self, field):
        label_str = field.label
        if not label_str:
            label_str = pretty_name(field.name)
        if self.form.label_suffix and label_str[-1] not in ':?.!':
            label_str += self.form.label_suffix
        return label_str

    def get_submit_row(self):
        return tr(td(attr(colspan=self.columns_count, cssc='center'), input(attr(type=u'submit', value=self.form.submit_button_text, name=u'submit'))))


class NestedFieldsetFormSectionLayout(FormLayout):
    def __init__(self, form, section_spec, *content, **kwd):
        super(NestedFieldsetFormSectionLayout, self).__init__(form, *content, **kwd)
        self.tag = u'fieldset'
        self.cssc = 'form_fieldset'
        self.section_spec = section_spec
        self.create_layout()

    def get_fields(self):
        section_fields_names = self.section_spec[2]
        return [item[1] for item in self.form.fields.items() if item[0] in section_fields_names]

    def get_fields_dict(self):
        section_fields_names = self.section_spec[2]
        return dict([item for item in self.form.fields.items() if item[0] in section_fields_names])

    def layout_start(self):
        section_name = self.section_spec[0]
        if section_name:
            self.add(legend(section_name))
        self.add(table(tagid('table'), attr(cssc="form_table")))

    def layout_fields(self):
        fields_in_section = self.get_fields()
        for field in fields_in_section:
            errors = self.form.errors.get(field.name_orig, None)
            self.table.add(tr(
                td(errors, field)))

    def create_layout(self):
        self.content = []
        self.layout_start()
        self.layout_fields()

    def get_label_name(self, field):
        label_str = field.label
        if not label_str:
            label_str = pretty_name(field.name)
        return label_str


class HideableNestedFieldsetFormSectionLayout(NestedFieldsetFormSectionLayout):
    def layout_start(self):
        section_name = self.section_spec[0]
        section_id = self.section_spec[1]
        link_id = "%s_display" % section_id
        if section_name:
            self.add(legend(section_name))
        self.add(div(
            attr(style="text-align: right; padding-right: 1em;"),
            a(
                "hide",
                attr(href="JavaScript:void();"),
                onclick="show_hide('%s', '%s');" % (section_id, link_id),
                id=link_id,
                title="Click to show or hide the fieldset contents.")))
        self.add(table(
            tagid('table'), attr(cssc="form_table"), id=section_id))


class DivFormSectionLayout(NestedFieldsetFormSectionLayout):
    def __init__(self, form, section_spec, *content, **kwd):
        super(DivFormSectionLayout, self).__init__(form, section_spec, *content, **kwd)
        self.tag = u'div'
        self.cssc = "test"
        self.style = "width: 300px;"
        self.section_spec = section_spec
        self.create_layout()

    def layout_start(self):
        pass

    def layout_fields(self):
        fields_in_section = self.get_fields()

        for field in fields_in_section:
            errors = self.form.errors.get(field.name_orig, None)
            self.add(errors, field)


class SimpleFieldsetFormSectionLayout(FormLayout):
    def __init__(self, form, section_spec, *content, **kwd):
        super(SimpleFieldsetFormSectionLayout, self).__init__(form, *content, **kwd)
        self.section_spec = section_spec
        self.tag = u'fieldset'
        self.layout_fields()

    def layout_fields(self):
        self.add(table(tagid("table")))
        self.add(legend(self.section_spec[0]))
        fields_in_section = self.get_fields()
        hidden_fields = []
        for field in fields_in_section:
            if field.is_hidden:
                hidden_fields.append(field)
                continue
            label_str = self.get_label_name(field)
            errors = self.form.errors.get(field.name_orig, None)
            self.table.add(tr(
                td(label_str),
                td(errors, field)))
        self.add(hidden_fields)

    def get_label_name(self, field):
        label_str = field.label
        if not label_str:
            label_str = pretty_name(field.name)
        return label_str

    def get_fields(self):
        section_fields_names = self.section_spec[2]
        return [item[1] for item in self.form.fields.items() if item[0] in section_fields_names]


class HideableSimpleFieldsetFormSectionLayout(SimpleFieldsetFormSectionLayout):
    def layout_fields(self):
        section_name = self.section_spec[0]
        section_id = self.section_spec[1]
        link_id = "%s_display" % section_id
        self.add(div(
            attr(style="text-align: right; padding-right: 1em;"),
            a(
                "hide",
                attr(href="JavaScript:void();"),
                onclick="show_hide('%s', '%s');" % (section_id, link_id),
                id=link_id)))
        self.add(table(tagid("table"), id=section_id))
        self.add(legend(section_name))
        fields_in_section = self.get_fields()
        hidden_fields = []
        for field in fields_in_section:
            if field.is_hidden:
                hidden_fields.append(field)
                continue
            label_str = self.get_label_name(field)
            errors = self.form.errors.get(field.name_orig, None)
            self.table.add(tr(
                td(label_str),
                td(errors, field)))
        self.add(hidden_fields)
