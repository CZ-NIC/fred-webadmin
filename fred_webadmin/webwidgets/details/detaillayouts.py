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

import types
from logging import debug

from fred_webadmin.webwidgets.gpyweb.gpyweb import tagid, attr, table, tbody, tr, td, label
from fred_webadmin.webwidgets.details.abstractdetaillayout import \
    AbstractDetailLayout
from fred_webadmin.webwidgets.details.sectionlayouts import SectionLayout


class DetailLayout(AbstractDetailLayout):
    pass


class TableDetailLayout(DetailLayout):
    columns_count = 2
    tattr_list = table.tattr_list

    def __init__(self, *content, **kwd):
        super(TableDetailLayout, self).__init__(*content, **kwd)
        self.tag = u'table'
        self.cssc = 'detail_table'
        if self.detail.is_nested:
            self.cssc = 'nested_' + self.cssc

        self.create_layout()

    def create_layout(self):
        detail = self.detail
        self.add(tbody(tagid('tbody')))

        for field in detail.fields.values():
            label_str = self.get_label_name(field)
            self.tbody.add(tr(td(attr(cssc='left_label'), label(label_str)),
                              td(field)
                             )
                          )


class SectionDetailLayout(TableDetailLayout):
    def create_section(self, section_spec):
        section_layout = SectionLayout
        if len(section_spec) > 2:
            section_layout = section_spec[2]
            # List of layouts, first for detail without history,
            # second for detail with history.
            if isinstance(section_layout, types.ListType):
                if not self.detail.history:
                    section_layout = section_layout[0]
                else:
                    section_layout = section_layout[1]
        return section_layout(self.detail, section_spec)

    def create_layout(self):
        self.add(tbody(tagid('tbody')))

        for section_spec in self.detail.sections:
            self.tbody.add(tr(td(self.create_section(section_spec))))


class DirectSectionDetailLayout(SectionDetailLayout):
    ''' Layout that renders section_layout detail directly (without any wrapper tag)'''
    def __init__(self, *content, **kwd):
        super(DirectSectionDetailLayout, self).__init__(*content, **kwd)
        self.tag = ''

    def create_layout(self):
        for section_spec in self.detail.sections:
            self.add(self.create_section(section_spec))


class TableColumnsDetailLayout(DetailLayout):
    def __init__(self, *content, **kwd):
        super(TableColumnsDetailLayout, self).__init__(*content, **kwd)
        self.tag = u''
        self.create_layout()

    def create_layout(self):
        detail = self.detail

        for field in detail.fields.values():
            self.add(td(field))


class TableRowDetailLayout(TableColumnsDetailLayout):
    tattr_list = tr.tattr_list

    def __init__(self, *content, **kwd):
        super(TableRowDetailLayout, self).__init__(*content, **kwd)
        self.tag = u'tr'


class OnlyFieldsDetailLayout(DetailLayout):
    ''' Detail, that renders only fields, directly without anything.
        Fields are separated by comma.
    '''
    def __init__(self, *content, **kwd):
        super(OnlyFieldsDetailLayout, self).__init__(*content, **kwd)
        self.tag = u''
        self.enclose_content = True
        self.create_layout()

    def create_layout(self):
        for i, field in enumerate(self.detail.fields.values()):
            if i != 0:
                self.add(',')
            self.add(field)
