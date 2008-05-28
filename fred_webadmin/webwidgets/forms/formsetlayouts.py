import sys
sys.path.insert(0, '')
from logging import debug

from fred_webadmin.translation import _
from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget, tagid, attr, notag, div, span, table, tbody, tr, th, td, input, label, select, option, ul, li, script, a, img, strong

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
        formset = self.formset
        
        self.add(tbody(tagid('tbody')))
        
        
        if formset.non_form_errors():
            self.tbody.add(tr(td(attr(colspan=self.columns_count), _('Errors:'), formset.non_form_errors())))
        
        for form in formset.forms:
            self.tbody.add(tr(
                              td(form)
                             )
                          )
        
        formset.add(formset.management_form.fields.values())
        if not formset.is_nested:
            self.tbody.add(self.get_submit_row())
        
    def get_submit_row(self):
        return tr(td(attr(colspan=self.columns_count, cssc='center'), input(attr(type=u'submit', value=u'Save set', name=u'submit'))))
      
