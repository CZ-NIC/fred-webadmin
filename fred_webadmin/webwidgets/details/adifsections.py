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
from fred_webadmin.webwidgets.gpyweb.gpyweb import attr, tr, td
from fred_webadmin.webwidgets.details.sectionlayouts import SectionLayout


class DatesSectionLayout(SectionLayout):
    def layout_fields(self):
        date_and_registrar_fields_names = [
            ['createDate', 'createRegistrar'],
            ['updateDate', 'updateRegistrar'],
            ['transferDate', None],
            ['expirationDate', None],
            ['valExDate', None],
            ['outZoneDate', None],
            ['deleteDate', None],
        ]
        date_and_registrar_fields = [
            [self.detail.fields.get(date_field_name), self.detail.fields.get(registrar_field_name)]
            for date_field_name, registrar_field_name in date_and_registrar_fields_names
        ]

        for [date_field, registrar_field] in date_and_registrar_fields:
            if not date_field:
                continue

            row = tr()

            if registrar_field:
                colspan_attr = attr()
                registrar_field.create_inner_detail()  # creates field.inner_detail
            else:
                colspan_attr = attr(colspan=3)

            label_str = self.get_label_name(date_field)
            row.add(td(attr(cssc='left_label'), label_str),
                    td(colspan_attr, date_field))
            if registrar_field:
                row.add(td(attr(cssc='left_label'), _('By registrar:')),
                        td(registrar_field.inner_detail.fields['handle_url'])
                       )
            self.tbody.add(row)
