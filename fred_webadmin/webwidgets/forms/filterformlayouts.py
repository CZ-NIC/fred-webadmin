#!/usr/bin/python
# -*- coding: utf-8 -*-

from copy import deepcopy
import simplejson
from logging import debug

from fred_webadmin.translation import _
import forms
import filterforms
from adiffields import CompoundFilterField
from fred_webadmin.webwidgets.gpyweb.gpyweb import (WebWidget, noesc, tagid,
    attr, notag, div, span, table, tbody, tr, th, td, input, label, select,
    option, ul, li, script, a, img, strong)
from fields import ChoiceField, BooleanField, HiddenField
from fred_webadmin.webwidgets.utils import SortedDict
from fred_webadmin.webwidgets.utils import escape_js_literal
from formlayouts import TableFormLayout

REPLACE_ME_WITH_LABEL = 'REPLACE_ME_WITH_LABEL'
REPLACE_ME_WITH_EMPTY_FORM = 'REPLACE_ME_WITH_EMPTY_FORM'

class UnionFilterFormLayout(TableFormLayout):
    columns_count = 1
    def __init__(self, form, *content, **kwd):
        super(UnionFilterFormLayout, self).__init__(form, *content, **kwd)
        self.add_css_class(u'unionfiltertable')
        self.id = u'unionfiltertable'
        self.media_files = ['/css/filtertable.css',
                          '/css/ext/css/ext-all.css',
                          '/js/logging.js',
                          '/js/ext/ext-base.js',
                          '/js/ext/ext-all.js'
                          ]

    def create_layout(self):
        self.content = []
        self.add(tbody(tagid('tbody')))
        form_count = len(self.form.forms)
        for i, inner_form in enumerate(self.form.forms):
            if i > 0 and i < form_count:
                self.tbody.add(tr(attr(cssc='or_row'), self.build_or_row()))
            self.tbody.add(tr(td(inner_form)))
        self.tbody.add(self.get_submit_row())
        self.tbody.add(script(attr(type='text/javascript'), noesc(self.union_form_js())))
        debug('After create unionlayout')

    def union_form_js(self):
        output = u'function buildOrRow() {\n'
        output += u"var row = '%s';\n" % escape_js_literal(unicode(self.build_or_row()))
        output += u'return row;\n'
        output += u'}\n\n'

        output += u'function buildForm() {\n'
        output += u"var row = '<td>';\n"
        output += u"row += getEmpty%s();\n" % self.form.form_class.__name__
        output += u"row += '</td>';\n"
        output += u'return row;\n'
        output += u'}\n\n'


        return output

    def build_or_row(self):
        return td(
            attr(cssc='or_cell', colspan=self.columns_count),
            input(attr(
                type="button", value="OR-", onclick="removeOr(this)",
                style="float: left;")),
            div(attr(style="padding-top: 0.3em"), 'OR'))

    def get_submit_row(self, hidden_fields=None):
        or_plus_button = input(attr(
            type="button", value="OR+", onclick="addOrForm(this)",
            style="float: left;"))
        save_input = input(attr(
            id='save_input', type="text", name="save_input",
            value=_('name'), disabled='disabled',
            style="float: left; margin-left: 0.4em; display:none;"))
        save_button = input(attr(
            type="button", value="Save", onclick="saveUnionForm(this)",
            style="float: left; margin-left: 0.4em"))
        submit_button = input(attr(
            type=u'button', value=u'OK', onclick='sendUnionForm(this)',
            style="float: right;"))
        return tr(attr(cssc='submit_row'), td(
            or_plus_button, save_input, save_button, hidden_fields,
            submit_button),)


class FilterTableFormLayout(TableFormLayout):
    columns_count = 3
    def __init__(self, form, *content, **kwd):
        self.field_counter = 0
        self.all_fields = []
        self.all_errors = {}
        super(FilterTableFormLayout, self).__init__(form, *content, **kwd)
        self.cssc = u'filtertable'

    def create_layout(self):
        self.content = []
        form = self.form
        self.add(tbody(tagid('tbody')))

        # Following block creates self.all_fields, self.errors and
        # non_field_errors from fields and their forms (if they are
        # compound fields) recursively (obtaining linear structure
        # from tree structure).
        non_field_errors = []
        # [names, labels, form or field], it is stack (depth-first-search)
        open_nodes = [[[], [], self.form]]

        while open_nodes:
            names, labels, tmp_node = open_nodes.pop()

            # Add errors from this tmp_node - for fields using composed name
            # and join all non_field_errors together.
            if isinstance(tmp_node, filterforms.FilterForm):
                if tmp_node.is_bound:
                    non_field_errors.extend(tmp_node.non_field_errors())
                    for error_name, error in tmp_node.errors.items():
                        if error_name == forms.NON_FIELD_ERRORS:
                            continue
                        self.all_errors['-'.join(names + [error_name])] = error

                # 'reversed': compensation for the reverse order onstack
                for field in reversed(tmp_node.fields.values()):
                    if not isinstance(field, CompoundFilterField):
                        open_nodes.append([names, labels, field])
                    else:
                        open_nodes.append([
                            names + [field.name],
                            labels + [field.label], field.form])
            else:
                filter_name = tmp_node.name
                composed_name = '-'.join(names + [filter_name])
                tmp_node.label = '.'.join(labels + [tmp_node.label])
                self.all_fields.append([composed_name, tmp_node])

        if non_field_errors:
            self.tbody.add(tr(td(
                attr(colspan=self.columns_count),
                'Errors:', form.non_field_errors())))

        self.tbody.add(tr(
            attr(cssc='filtertable_header'), th(attr(colspan='2'),
            self.form._get_header_title()),
            th(div(attr(cssc='for_fields_button extjs')))))

        for composed_name, field in self.all_fields:
            errors = self.all_errors.get(composed_name, None)
            self.tbody.add(tr(
                attr(cssc='field_row ' + composed_name),
                self.build_field_row(field, errors)))
        self.add(script(
            attr(type='text/javascript'),
            'filterObjectName = "%s"' % self.form.get_object_name())) # global javascript variable
        self.tbody.add(self.build_fields_button())

    def build_field_row(self, field, errors=None, for_javascript=False):
        if for_javascript:
            label_str = REPLACE_ME_WITH_LABEL + ':'
        else:
            label_str = self.get_label_name(field)

        negation_field = BooleanField('negation|' + field.name, field.negation)
        if for_javascript:
            # Needed for detecting presence of fields such as checkboxes
            # and multiple selects, because they do not send data if they
            # are not checked or no option is selected.
            presention_field = HiddenField('presention|' + field.name, 'on')
        else:
            # Dtto.
            presention_field = HiddenField('presention|' + field.name, '%03d' % self.field_counter)
            self.field_counter += 1

        if not isinstance(field, CompoundFilterField):
            return notag(
                td(attr(cssc='label_cell'), label(label_str)), td(presention_field, errors, field),
                td(negation_field, label('NOT')))

    def build_fields_button(self):
        pass

    def get_javascript_gener_field(self):
        # --- function createRow and variable allFieldsDict---

        output = u'function createRow%s(fieldName, fieldLabel) {\n' % self.form.get_object_name()
        output += u'var row = "";\n'

        output += u'switch (fieldName) {\n'
        base_fields = deepcopy(self.form.base_fields)
        output += u"default:\n" # if not specified, first field is taken
        fields_js_dict = SortedDict()
        for field_num, (name, field) in enumerate(base_fields.items()):
            field.name = name
            output += u"case '%s':\n" % name
            rendered_field = unicode(
                self.build_field_row(
                    field, for_javascript=True))
            rendered_field = escape_js_literal(rendered_field)
            output += u"    row += '%s';\n" % rendered_field
            if isinstance(field, CompoundFilterField):
                output += u"    row = row.replace(/%s/g, getEmpty%s());\n" % (REPLACE_ME_WITH_EMPTY_FORM, field.form_class.__name__)
                fields_js_dict[name] = {'label': field.label, 'fieldNum': field_num, 'formName': field.form_class.get_object_name()}
            else:
                fields_js_dict[name] = {'label': field.label, 'fieldNum': field_num}
            output += u"    break;\n"
        output += u'}\n' # end of switch
        output += u'row = row.replace(/%s/g, fieldLabel);\n' % REPLACE_ME_WITH_LABEL
        output += u'return row;\n'
        output += u'}\n' # end of createRow function

        return (output, fields_js_dict)
