#!/usr/bin/python
# -*- coding: utf-8 -*-

from copy import copy, deepcopy

from gpyweb.gpyweb import WebWidget, tagid, attr, notag, table, tbody, tr, th, td, input, label, select, option, ul, li, script, a, img, strong
from fields import ChoiceField, BooleanField, HiddenField
from adiffields import CompoundFilterField
from fred_webadmin.translation import _
from utils import pretty_name, escape_js_literal

FIELD_COUNTER_VALUE = 'FIELD_COUNTER_VALUE'
REPLACE_ME_WITH_EMPTY_FORM = 'REPLACE_ME_WITH_EMPTY_FORM'

class FormLayout(WebWidget):
    pass

class TableFormLayout(FormLayout):
    columns_count = 2
    tattr_list = table.tattr_list
    def __init__(self, form, *content, **kwd):
        super(TableFormLayout, self).__init__(*content, **kwd)
        self.tag = u'table'
        self.form = form
        self.create_layout()
        self.media_files.append('/css/filtertable.css')
        
    
    def create_layout(self):
        form = self.form
        self.add(tbody(tagid('tbody')))
        
        if form.non_field_errors():
            self.tbody.add(tr(td(attr(colspan=self.columns_count), 'Errors:', form.non_field_errors())))
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
        return tr(td(attr(colspan=self.columns_count), hidden_fields, input(attr(type=u'submit', value=u'OK', name=u'submit'))))
      
class UnionFilterFormLayout(TableFormLayout):
    def __init__(self, form, *content, **kwd):
        super(UnionFilterFormLayout, self).__init__(form, *content, **kwd)
        self.cssc = u'unionfiltertable'
        
    def create_layout(self):
        self.add(tbody(tagid('tbody')))
        
        form_count = len(self.form.forms)
        for i, inner_form in enumerate(self.form.forms):
            if i > 0 and i < form_count:
                self.tbody.add(tr(attr(cssc='or_row'), self.build_or_row()))
            self.tbody.add(tr(td(inner_form)))
        self.tbody.add(tr(#attr(cssc='filtertable_row'),
                    td(attr(cssc='add_or_cell'),
                       strong('OR'), 
                       a(attr(cssc='pointer_cursor', onclick='addOrForm(this)'), 
                         img(src='/img/icons/green_plus.gif')))
                   )
                )
        self.tbody.add(self.get_submit_row())

        self.tbody.add(script(attr(type='text/javascript'), self.union_form_js()))
        print "za create uionlayout"
            
    def union_form_js(self):
        output = u'function buildOrRow() {\n'
        output += u"var row = '%s';\n" % escape_js_literal(unicode(self.build_or_row()))
        output += u'return row;\n'
        output += u'}\n\n'
        
        output += u'function buildForm() {\n'
        output += u"var row = '<td>';\n"
        output += u"row += getEmpty%s();\n" % self.form.form_class.__name__  # % unicode(self.form.form_class()).replace('\n', '\\n\\\n')
        output += u"row += '</td>';\n"
#        output += u"var row = '<td>ahoj</td>';\n"
        output += u'return row;\n'
        output += u'}\n\n'
        

        return output
            
    def build_or_row(self):
        #return tr(attr(cssc='or_row'), td(attr(colspan=self.columns_count), 'OR'))
        return td(attr(cssc='or_cell', colspan=self.columns_count), 'OR')
            
    def get_submit_row(self, hidden_fields=None):
        submit_button = input(attr(type=u'button', value=u'OK', onclick='sendUnionForm()'))
        return tr(attr(cssc='submit_row'), td(attr(colspan=2), hidden_fields, submit_button))
        
class FilterTableFormLayout(TableFormLayout):
    columns_count = 4    
    def __init__(self, form, *content, **kwd):
        self.field_counter = 0
        super(FilterTableFormLayout, self).__init__(form, *content, **kwd)
        self.cssc = u'filtertable'
        
        
        
    def create_layout(self):
        form = self.form
        self.add(tbody(tagid('tbody')))
        
        if form.non_field_errors():
            self.tbody.add(tr(td(attr(colspan=self.columns_count), 'Errors:', form.non_field_errors())))
        
        if not self.form.is_nested:
            self.tbody.add(tr(attr(cssc='filtertable_header'), th(_('Filter name')), th(_('Neg.')), th(_('Value')), th()))

        hidden_fields = []
        for field in form.fields.values():
            self.tbody.add(tr(attr(cssc='field_row'), self.build_field_row(field, hidden_fields)))
        self.tbody.add(self.build_and_row())
        
        

    def get_field_chooser(self):
        print 'KEYS %s' % self.form.fields.keys()
        print 'BFS %s' % self.form.base_fields.keys()
        fields = [field_name.split('|')[1] for field_name in self.form.fields.keys()]
        field_choices = [(name, self.get_label_name(field)) for name, field in self.form.base_fields.items() if name not in fields]
        print 'FC %s' % field_choices
        return ChoiceField(choices=field_choices)
    
        
    def build_field_row(self, field, hidden_fields=None, for_javascript=False):#, field_chooser_value=None):
        if field.is_hidden:
            if hidden_fields is not None:
                hidden_fields.append(field)
            return ''
        

        errors = self.form.errors.get(field.name, None)

#        current_field_chooser = self.get_field_chooser()
#        if field_chooser_value:
#            current_field_chooser.value = field_chooser_value
#        else:
#            current_field_chooser.value = field.name.split('|')[3]
        field_name = field.name.split('|')[1]
        label_str = self.get_label_name(field)
        negation_field = BooleanField(field.name.replace('filter', 'negation'), field.negation)
        del_row_td = td(a(attr(cssc='pointer_cursor', onclick=u"delRow(this, '%s', '%s')" % (field_name, label_str)), img(src='/img/icons/purple_minus.gif')))
        if for_javascript:
            presention_field = HiddenField(field.name.replace('filter', 'presention'), FIELD_COUNTER_VALUE) # needed for detecting presention of fields as checkboxes and multiple selects, because they do not send data if nonchecket or selected no option
        else: 
            presention_field = HiddenField(field.name.replace('filter', 'presention'), '%03d' % self.field_counter) # needed for detecting presention of fileds as checkboxes and multiple selects, because they do not send data if nonchecket or selected no option 
            self.field_counter += 1

        if not isinstance(field,  CompoundFilterField):
            return notag(td(label_str),
                         td(presention_field, negation_field),
                         td(errors, field),
                         del_row_td
                        )
        else:
            if for_javascript:
                field = REPLACE_ME_WITH_EMPTY_FORM
            return notag(td(attr(colspan=self.columns_count-1),
                            label_str, presention_field, negation_field, errors,
                            field
                           ),
                         del_row_td
                        )
        
            
                
    def build_and_row(self):
        field_chooser = self.get_field_chooser()
        
        if not field_chooser.choices:
            style = 'visibility: hidden'
        else:
            style = ''
        
        return tr(attr(cssc='and_row'),
                  td(attr(colspan=self.columns_count), 
#                     ChoiceField(choices=(('AND', 'AND'), ('OR', 'OR'))),
                     strong('AND'),
#                     a(attr(href=u'javascript:addRow(this)'), u'+')))
                     field_chooser,
                     a(attr(cssc='pointer_cursor', onclick="addRow(this, '%s')" % self.form.__class__.__name__), img(src='/img/icons/green_plus.gif'))))
    

        
    def get_javascript_gener_field(self):
        # --- function createRow ---
        output = u'function createRow%s(fieldName, fieldNum) {\n' % self.form.__class__.__name__
        output += u'var row = "";\n'

        output += u'switch (fieldName) {\n'
        base_fields = deepcopy(self.form.base_fields)
        output += u"default:\n" # if not specified, first field is taken
        for name, field in base_fields.items():
            field.name = u'filter|' + name
            output += u"case '%s':\n" % name
            rendered_field = unicode(self.build_field_row(field, for_javascript=True))
            rendered_field = escape_js_literal(rendered_field)
            output += u"    row += '%s';\n" % rendered_field
            if isinstance(field, CompoundFilterField):
                output += u"    row = row.replace(/%s/g, getEmpty%s());\n" % (REPLACE_ME_WITH_EMPTY_FORM, field.form_class.__name__)
            output += u"    break;\n"
        output += u'}\n'
        
        
        # replaces field counter value with row num in form (it is there to be able to sort form field in order that user created them:
        output += u'row = row.replace(/%s/g, fieldNum);\n' % FIELD_COUNTER_VALUE
        output += u'return row;\n'
        output += u'}\n\n'
        
#        output += u"""
#            function addRow%(form_name)s(thisElem, name) {
#                var my_tr = getFirstParentByTagAndClassName(thisElem, tagName='tr');
#                var name = getNameToAdd(my_tr)
#                var fieldNum = getNewFieldNum(thisElem);
#                var new_tr = TR({'class': 'field_row'});
#                insertSiblingNodesBefore(my_tr, new_tr);
#                
#                new_tr.innerHTML = createRow%(form_name)s(name, fieldNum);
#                fieldChooser = getFirstElementByTagAndClassName('select', '', my_tr);
#                fieldChooser.remove(name);
#                if (fieldChooser.length <= 0) {
#                    //my_tr.parentNode.removeChild(my_tr);\
#                    log('vypinam vysibylyty of my_tr);
#                    my_tr.style.visibility = 'hidden';
#                }
#                
#                
#                return null;
#            }
#            
#        """ % {'form_name': self.form.__class__.__name__}
        return output
    