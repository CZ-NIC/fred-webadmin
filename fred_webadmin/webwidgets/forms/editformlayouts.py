from logging import debug

from fred_webadmin.translation import _
import forms
import editforms
from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget, tagid, attr, notag, div, span, table, tbody, tr, th, td, input, label, select, option, ul, li, script, a, img, strong
from formlayouts import TableFormLayout, FormLayout

class EditFormLayout(TableFormLayout):
    columns_count = 2
    def __init__(self, form, *content, **kwd):
        super(EditFormLayout, self).__init__(form, *content, **kwd)
        if self.cssc:
            self.cssc += u' editform_table'
        else:
            self.cssc = u'editform_table'

        self.media_files = ['/css/editform.css',
                          '/js/ext/ext-base.js',
                          '/js/ext/ext-all.js',
                          '/js/editform.js',
                          '/js/logging.js',
                         ]

    def create_layout(self):
        super(EditFormLayout, self).create_layout()

    def get_submit_row(self, hidden_fields=None):
        return tr(td(attr(colspan=self.columns_count, cssc='center'),
                     hidden_fields,
                     input(attr(type=u'submit', value=_(u'Save'), name=u'submit'))
                    ))

class RegistrarEditFormLayout(FormLayout):
    def __init__(self, form, *content, **kwd):
        super(RegistrarEditFormLayout, self).__init__(form, *content, **kwd)
        self.tag = u'div'
        self.create_layout()

    def create_layout(self):
        self.content = []
        form = self.form

        if form.non_field_errors():
            self.add(div(_('Errors:'), form.non_field_errors()))
        hidden_fields = []

        for index, section in enumerate(form.sections):
            section_layout_class = section[-1]
            self.add(div(
                attr(cssc="editform"), section_layout_class(form, section)))

        self.add(hidden_fields)
        if not form.is_nested:
            self.add(self.get_submit_row())

    def get_submit_row(self):
        return div(attr(cssc='center'),
            input(attr(type=u'submit', value=u'Save', name=u'submit')))
