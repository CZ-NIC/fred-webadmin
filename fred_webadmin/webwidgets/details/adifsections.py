from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget, tagid, attr, notag, div, span, table, caption, tbody, tr, th, td, input, label, select, option, ul, li, script, a, img, strong
from fred_webadmin.webwidgets.details.sectionlayouts import SectionLayout
from fred_webadmin.translation import _

class DatesSectionLayout(SectionLayout):
    def layout_fields(self):
        #fields_in_section = self.get_fields()
        
#        for field in fields_in_section:
#            field.create_inner_detail() # creates field.inner_detail
#            label_str = self.get_label_name(field)
#            #import pdb; pdb.set_trace()
#            self.tbody.add(tr(td(attr(cssc='left_label'), label_str),
#                              td(field.inner_detail.fields['name']),
#                              td(field.inner_detail.fields['email'])
#                             )) 
        
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

        for i, [date_field, registrar_field] in enumerate(date_and_registrar_fields):
            if not date_field:
                continue
            
            row = tr()
            
            if registrar_field:
                colspan_attr = attr()
                registrar_field.create_inner_detail() # creates field.inner_detail
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
        
        
#        if transfer_date_field:
#            label_str = self.get_label_name(transfer_date_field)
#            self.tbody.add(tr(td(attr(cssc='left_label'), label_str),
#                              td(attr(colspan='3'), transfer_date_field)))
        

                
            
        