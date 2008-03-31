#!/usr/bin/python
# -*- coding: utf-8 -*-

from copy import deepcopy
import simplejson

from fred_webadmin.webwidgets.utils import SortedDict
from gpyweb.gpyweb import WebWidget, tagid, attr, notag, div, span, table, tbody, tr, th, td, input, label, select, option, ul, li, script, a, img, strong
from fields import ChoiceField, BooleanField, HiddenField
#from fred_webadmin.webwidgets.adifforms import FilterForm
import forms
import adifforms
from adiffields import CompoundFilterField
from fred_webadmin.translation import _
from utils import pretty_name, escape_js_literal


#FIELD_COUNTER_VALUE = 'FIELD_COUNTER_VALUE'
REPLACE_ME_WITH_LABEL = 'REPLACE_ME_WITH_LABEL'
REPLACE_ME_WITH_EMPTY_FORM = 'REPLACE_ME_WITH_EMPTY_FORM'

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
        return tr(td(attr(colspan=self.columns_count, cssc='center'), hidden_fields, input(attr(type=u'submit', value=u'OK', name=u'submit'))))
      
class UnionFilterFormLayout(TableFormLayout):
    columns_count = 1
    def __init__(self, form, *content, **kwd):
        super(UnionFilterFormLayout, self).__init__(form, *content, **kwd)
        self.cssc = u'unionfiltertable'
        self.id = u'unionfiltertable'
        self.media_files=['/css/filtertable.css', '/css/ext/css/ext-all.css', '/js/ext/ext-base.js', '/js/ext/ext-all.js']
        
    def create_layout(self):
        self.add(tbody(tagid('tbody')))
        
        form_count = len(self.form.forms)
        for i, inner_form in enumerate(self.form.forms):
            if i > 0 and i < form_count:
                self.tbody.add(tr(attr(cssc='or_row'), self.build_or_row()))
            self.tbody.add(tr(td(inner_form)))
#        self.tbody.add(tr(#attr(cssc='filtertable_row'),
#                    td(attr(cssc='add_or_cell'),
#                       strong('OR'),
#                       a(attr(cssc='pointer_cursor', onclick='addOrForm(this)'), 
#                         img(src='/img/icons/green_plus.gif')))
#                   )
#                )
        self.tbody.add(self.get_submit_row())
        self.add(script(attr(type='text/javascript'), 'Ext.onReady(function () {addFieldsButtons()})')) 

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
        #return td(attr(cssc='or_cell', colspan=self.columns_count), 'OR')
        return td(attr(cssc='or_cell', colspan=self.columns_count), input(attr(type="button", value="OR-", onclick="removeOr(this)", style="float: left;")), div(attr(style="padding-top: 0.3em"), 'OR'))
            
    def get_submit_row(self, hidden_fields=None):
        or_plus_button = input(attr(type="button", value="OR+", onclick="addOrForm(this)", style="float: left;"))
        save_input = input(attr(id='save_input', type="text", name="save_input", value=_('name'), disabled='disabled', style="float: left; margin-left: 0.4em; display:none;"))
        save_button = input(attr(type="button", value="Save", onclick="saveUnionForm(this)", style="float: left; margin-left: 0.4em"))
        submit_button = input(attr(type=u'button', value=u'OK', onclick='sendUnionForm(this)', style="float: right;"))
#        submit_button = input(attr(type=u'submit', value=u'OK', style="float: right;"))
        return tr(attr(cssc='submit_row'), 
                  td(or_plus_button, save_input, save_button, hidden_fields, submit_button),
                 )

        
class FilterTableFormLayout(TableFormLayout):
    columns_count = 3
    def __init__(self, form, *content, **kwd):
        self.field_counter = 0
        self.all_fields = []
        self.all_errors = {}
        super(FilterTableFormLayout, self).__init__(form, *content, **kwd)
        self.cssc = u'filtertable'
        
    def create_layout(self):
        form = self.form
        self.add(tbody(tagid('tbody')))

        # following block creates self.all_fields, self.errors and non_field_errors from fields and their forms (if they are compound fields) recursively
        # (obtaining linear structure from tree structure)
        non_field_errors = []
        open_nodes = [[[], [], self.form]] # [names, labels, form or field], it is stack (depth-first-search) 
        
        while open_nodes:
#            import pdb; pdb.set_trace()
            names, labels, tmp_node = open_nodes.pop()
            
            #add errors from this tmp_node - for fields using composed name and join all non_field_errors together
            if isinstance(tmp_node, adifforms.FilterForm):
                if tmp_node.is_bound:
                    non_field_errors.extend(tmp_node.non_field_errors())
                    for error_name, error in tmp_node.errors.items():
                        if error_name == forms.NON_FIELD_ERRORS:
                            continue
                        error_filter_name = error_name.split('|')[1]
                        self.all_errors['-'.join(names + [error_filter_name])] = error
            
                for field in reversed(tmp_node.fields.values()): # 'reversed': because order in stack will be reversed, so to companate it
                    filter_name = field.name.split('|')[1]
                    if not isinstance(field,  CompoundFilterField):
                        open_nodes.append([names, labels, field])
                    else:
                        open_nodes.append([names + [filter_name], labels + [field.label], field.form])
            else:
                filter_name = tmp_node.name.split('|')[1]
                composed_name = '-'.join(names + [filter_name])
                tmp_node.label = '.'.join(labels + [tmp_node.label])
                self.all_fields.append([composed_name, tmp_node])
        
        if non_field_errors:
            self.tbody.add(tr(td(attr(colspan=self.columns_count), 'Errors:', form.non_field_errors())))
        
        self.tbody.add(tr(attr(cssc='filtertable_header'), 
                          th(attr(colspan='2'), _(self.form.__class__.__name__[:-len('FilterForm')])), 
                          th(div(attr(cssc='for_fields_button extjs')))))

        for composed_name, field in self.all_fields:
            errors = self.all_errors.get(composed_name, None)
            self.tbody.add(tr(attr(cssc='field_row ' + composed_name), self.build_field_row(field, errors)))
        self.add(script(attr(type='text/javascript'), 'filterObjectName = "%s"' % self.form.get_object_name())) # global javascript variable
        self.tbody.add(self.build_fields_button())

#    def get_field_chooser(self):
#        print 'KEYS %s' % self.form.fields.keys()
#        print 'BFS %s' % self.form.base_fields.keys()
#        fields = [field_name.split('|')[1] for field_name in self.form.fields.keys()]
#        field_choices = [(name, self.get_label_name(field)) for name, field in self.form.base_fields.items() if name not in fields]
#        print 'FC %s' % field_choices
#        return ChoiceField(choices=field_choices)
        
    def build_field_row(self, field, errors = None, for_javascript=False):#, field_chooser_value=None):
        

        if for_javascript:
            label_str = REPLACE_ME_WITH_LABEL + ':'
        else:
            label_str = self.get_label_name(field)
        
        negation_field = BooleanField(field.name.replace('filter', 'negation'), field.negation)
        #del_row_td = td(a(attr(cssc='pointer_cursor', onclick=u"delRow(this, '%s', '%s')" % (field_name, label_str)), img(src='/img/icons/purple_minus.gif')))
        if for_javascript:
            presention_field = HiddenField(field.name.replace('filter', 'presention'), 'on') # needed for detecting presention of fields as checkboxes and multiple selects, because they do not send data if nonchecket or selected no option
        else: 
            presention_field = HiddenField(field.name.replace('filter', 'presention'), '%03d' % self.field_counter) # needed for detecting presention of fileds as checkboxes and multiple selects, because they do not send data if nonchecket or selected no option 
            self.field_counter += 1

        if not isinstance(field,  CompoundFilterField):
            return notag(td(label_str),
                         td(presention_field, errors, field),
                         td(negation_field, 'NOT')
                        )
        
            
    def build_fields_button(self): 
        pass
    
#    def build_and_row(self):
#        field_chooser = self.get_field_chooser()
#        
#        if not field_chooser.choices:
#            style = 'visibility: hidden'
#        else:
#            style = ''
#        
#        return tr(attr(cssc='and_row'),
#                  td(attr(colspan=self.columns_count), 
##                     ChoiceField(choices=(('AND', 'AND'), ('OR', 'OR'))),
#                     strong('AND'),
##                     a(attr(href=u'javascript:addRow(this)'), u'+')))
#                     field_chooser,
#                     a(attr(cssc='pointer_cursor', onclick="addRow(this, '%s')" % self.form.__class__.__name__), img(src='/img/icons/green_plus.gif'))))
    

        
    def get_javascript_gener_field(self):
        # --- function createRow ---
        
        output = u'function createRow%s(fieldName, fieldLabel) {\n' % self.form.get_object_name()
        output += u'var row = "";\n'

        output += u'switch (fieldName) {\n'
        base_fields = deepcopy(self.form.base_fields)
        output += u"default:\n" # if not specified, first field is taken
        fields_js_dict = SortedDict()
        for field_num, (name, field) in enumerate(base_fields.items()):
            field.name = u'filter|' + name
            output += u"case '%s':\n" % name
            rendered_field = unicode(self.build_field_row(field, for_javascript=True))
            rendered_field = escape_js_literal(rendered_field)
            output += u"    row += '%s';\n" % rendered_field
            if isinstance(field, CompoundFilterField):
                output += u"    row = row.replace(/%s/g, getEmpty%s());\n" % (REPLACE_ME_WITH_EMPTY_FORM, field.form_class.__name__)
                fields_js_dict[name] = {'label': field.label, 'fieldNum': field_num, 'formName': field.form_class.get_object_name()}#, 'createRowFunction': 'createRow%s' % self.form.get_object_name()}
            else:
                fields_js_dict[name] = {'label': field.label, 'fieldNum': field_num}
            output += u"    break;\n"
        output += u'}\n' # end of switch
        output += u'row = row.replace(/%s/g, fieldLabel);\n' % REPLACE_ME_WITH_LABEL
        output += u'return row;\n'
        output += u'}\n' # end of createRow function
        
        
        # replaces field counter value with row num in form (it is there to be able to sort form field in order that user created them:
#        output += u'row = row.replace(/%s/g, fieldNum);\n' % FIELD_COUNTER_VALUE
#        output += u'return row;\n'
#        output += u'}\n\n'
        
        return (output, fields_js_dict)
    