#!/usr/bin/python
# -*- coding: utf-8 -*-

from logging import debug

from fred_webadmin.translation import _
from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget, tagid, attr, notag, div, span, table, caption, tbody, tr, th, td, input, label, select, option, ul, li, script, a, img, strong
from fred_webadmin.webwidgets.utils import pretty_name

class DetailLayout(WebWidget):
    pass

class TableDetailLayout(DetailLayout):
    columns_count = 2
    tattr_list = table.tattr_list
    def __init__(self, detail, *content, **kwd):
        super(TableDetailLayout, self).__init__(*content, **kwd)
        self.tag = u'table'
        self.cssc = 'detail_table'
        self.detail = detail
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
        
    def get_label_name(self, field):
        label_str = field.label
        if not label_str:
            label_str = pretty_name(field.name)
        if self.detail.label_suffix and label_str[-1] not in ':?.!':
            label_str += self.detail.label_suffix
        return label_str
    
      
class SectionDetailLayout(TableDetailLayout):
    def create_layout(self):
        detail = self.detail
        self.add(tbody(tagid('tbody')))
        for section_name, section_fields_names in detail.sections:
            sec_table = table()
            if section_name:
                sec_table.add(caption(section_name + ':'))
            sec_table.add(tbody(tagid('tbody')))

            fields_in_section = [item[1] for item in detail.fields.items() if item[0] in section_fields_names]
            for field in fields_in_section:
                label_str = self.get_label_name(field)
                sec_table.tbody.add(tr(td(attr(cssc='left_label'), label_str),
                                       td(field)
                                      ))
            self.tbody.add(tr(td(sec_table)))
            
            