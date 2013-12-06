from fred_webadmin.webwidgets.gpyweb.gpyweb import attr, tr, th, td
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
                row.add(th('by_registrar:'),
                        td(registrar_field.inner_detail.fields['handle_url'])
                       )
            self.tbody.add(row)
