from logging import debug

from fred_webadmin.translation import _
import forms
import editforms
from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget, tagid, attr, notag, div, span, table, tbody, tr, th, td, input, label, select, option, ul, li, script, a, img, strong
from formlayouts import TableFormLayout

class EditFormLayout(TableFormLayout):
    columns_count = 2
    def __init__(self, form, *content, **kwd):
        super(EditFormLayout, self).__init__(form, *content, **kwd)
        if self.cssc:
            self.cssc += u' editform_table'
        else:
            self.cssc = u'editform_table'
            
        self.media_files=['/css/editform.css',
                          '/js/ext/ext-base.js',
                          '/js/ext/ext-all.js',
                          '/js/editform.js', 
                          '/js/logging.js', 
                         ]
        
    def create_layout(self):
#        form = self.form
#        for field in form.fields.values():
#            field.title = field.value
        super(EditFormLayout, self).create_layout()

#        self.add(tbody(tagid('tbody')))
#        
#        if form.non_field_errors():
#            self.tbody.add(tr(td(attr(colspan=self.columns_count), _('Errors:'), form.non_field_errors())))
#        hidden_fields = []
#        for field in form.fields.values():
#            if field.is_hidden:
#                hidden_fields.append(field)
#                continue
#            
#            label_str = self.get_label_name(field)
#            
#            if field.required:
#                cell_tag = th
#            else:
#                cell_tag = td
#            
#            errors = form.errors.get(field.name, None)
#                
#            self.tbody.add(tr(cell_tag(label(label_str)),
#                              td(errors, field)
#                             )
#                          )
#        
#        self.tbody.add(self.get_submit_row(hidden_fields))
    
    
    def get_submit_row(self, hidden_fields=None):
        return tr(td(attr(colspan=self.columns_count, cssc='center'), 
                     hidden_fields, 
                     input(attr(type=u'submit', value=_(u'Save'), name=u'submit'))
                    ))


class RegistrarEditFormLayout(TableFormLayout):
    def __init__(self, form, *content, **kwd):
        super(RegistrarEditFormLayout, self).__init__(form, *content, **kwd)

    def create_layout(self):
        form = self.form

        if form.non_field_errors():
            self.add(tr(td(_('Errors:'), form.non_field_errors())))
        hidden_fields = []

        for index, section in enumerate(form.sections):
            section_layout_class = section[-1]
            self.add(tr(td(section_layout_class(form, section))))

        self.add(hidden_fields)
        if not form.is_nested:
            self.add(self.get_submit_row())

    def get_submit_row(self):
        return tr(td(
            attr(colspan=self.columns_count, cssc='center'), 
            input(attr(type=u'submit', value=u'Save', name=u'submit'))))



