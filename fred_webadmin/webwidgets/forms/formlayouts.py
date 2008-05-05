#!/usr/bin/python
# -*- coding: utf-8 -*-

from logging import debug

from fred_webadmin.translation import _
from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget, tagid, attr, notag, div, span, table, tbody, tr, th, td, input, label, select, option, ul, li, script, a, img, strong
from fred_webadmin.webwidgets.utils import pretty_name

class FormLayout(WebWidget):
    pass

class TableFormLayout(FormLayout):
    columns_count = 2
    tattr_list = table.tattr_list
    def __init__(self, form, *content, **kwd):
        super(TableFormLayout, self).__init__(*content, **kwd)
        self.tag = u'table'
        self.cssc = 'form_table'
        self.form = form
        self.create_layout()
    
    def create_layout(self):
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
            
            errors = form.errors.get(field.name, None)
                
            self.tbody.add(tr(cell_tag(label(label_str)),
                              td(errors, field)
                             )
                          )
        
        self.tbody.add(self.get_submit_row(hidden_fields))

        
    def get_label_name(self, field):
        label_str = field.label
        if not label_str:
            label_str = pretty_name(field.name)
        if self.form.label_suffix and label_str[-1] not in ':?.!':
            label_str += self.form.label_suffix
        return label_str
    
    def get_submit_row(self, hidden_fields=None):
        return tr(td(attr(colspan=self.columns_count, cssc='center'), hidden_fields, input(attr(type=u'submit', value=u'OK', name=u'submit'))))
      
