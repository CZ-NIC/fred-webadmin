#!/usr/bin/python
# -*- coding: utf-8 -*-

from copy import copy, deepcopy
import cherrypy
import simplejson

from fred_webadmin import config
from forms import Form, SortedDictFromList
from fields import *
from adiffields import *
from formlayouts import FilterTableFormLayout, UnionFilterFormLayout
from fred_webadmin import config 
from fred_webadmin.translation import _
from utils import SortedDict, ErrorDict, escape_js_literal

#__all__ = ['LoginForm', 'FilterForm']

class LoginForm(Form):
    corba_server = ChoiceField(choices=[(str(i), ior.split('::')[1]) for i, ior in enumerate(config.iors)], label=_("Server"))
    login = CharField(max_length=30, label=_('Username'))#, initial=_(u'ohíňěček ťůříšekňú'))
    password = PasswordField(max_length=30, media_files='holahola.js')
    next = HiddenField(initial='/')
    media_files = 'form_files.js'

class UnionFilterForm(Form):
    'Form that contains more Filter Forms, data for this form is list of data for its Filter Forms'
    tattr_list = []
    def __init__(self, data=None, initial=None, layout=UnionFilterFormLayout, form_class=None, *content, **kwd):
        print "VYTVARIM UNIONFORM"
        if not form_class:
            raise RuntimeError('You have to specify form_class for UnionFilterForm!')

        if data:
            print 'data:%s' % data
            if data.has_key('json_data'):
                print 'data jsou json, takze je trasnvormuju'
                data = simplejson.loads(data['json_data'])
            else: print 'data nejsou json'

        self.form_class = form_class
        self.forms = []
        super(UnionFilterForm, self).__init__(data, initial=initial, layout=layout, *content, **kwd)
        
        
        if data is None: # if not bound, then create one empty dictionary
            self.forms.append(form_class())
        else: # else create form for each value in 'data' list
            for form_data in data:
                print 'vytvarim form v unionu s daty: %s' % form_data
                form = form_class(form_data)
                self.forms.append(form)
    
    def is_empty(self, exceptions=None):
        for form in self.forms:
            if form.is_empty(exceptions):
                return False
        return True
    
    def full_clean(self):
        self._errors = ErrorDict()
        if not self.is_bound: # Stop further processing.
            return
        self.cleaned_data = []
        
        for form in self.forms:
            print 'FORM %s' % repr(form)
            print 'FORM.errors %s' % repr(form.errors)
            self._errors.update(form.errors)
            if hasattr(form, 'cleaned_data'):
                self.cleaned_data.append(form.cleaned_data)
        
        if self._errors:
            delattr(self, 'cleaned_data')
            
class FilterForm(Form):
    "Form for one coumpund filter (e.g. Domains Filter)"
    default_fields_names = []
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':', layout=FilterTableFormLayout,
                 is_nested = False,
                 *content, **kwd):
        for field in self.base_fields.values():
            field.required = False
            field.negation = False
        
        super(FilterForm, self).__init__(data, files, auto_id, prefix, initial, error_class, label_suffix, layout, *content, **kwd)
        self.is_nested = is_nested
        self.media_files = ['/js/filtertable.js', '/js/MochiKit/MochiKit.js', '/js/scw.js', '/js/interval_fields.js', '/js/scwLanguages.js']
        self.layout = layout
        self.filter_base_fields()
        self.build_fields()
        self.tag = None
    
    def filter_base_fields(self):
        "Filters base fields against user negative permissions, so if user has nperm on field we delete it from base_fields (only in istance of FilterForm class)"
        user = cherrypy.session.get('user', None)
        
        object_name = self.__class__.__name__.lower().rsplit('filterform', 1)[0]
        self.base_fields = SortedDict([(name, field) for name, field in self.base_fields.items() 
                                       if not user.has_nperm('%s.%s.%s' % (object_name, 'filter', field.name))
                                      ])
        self.default_fields_names = [field_name for field_name in self.default_fields_names if field_name in self.base_fields.keys()]

                 
    
    def build_fields(self):
        '''
        Creates self.fields from given data or set default field (if not is_bound)
        Data for filter forms are in following format: list of dictionaries, 
        where between each dictionary is OR. In dictionary, key is name of field and 
        value is value of that field. If field is compound filter, then value is again
        dictionary.
        '''
        self.fields = SortedDict()
        if self.is_bound:
            fields_for_sort = {}
                            
            print "DATA", self.data
            for name_str in self.data.keys():
                name = name_str.split('|')
                if len(name) >= 2 and name[0] == 'presention':
                    filter_name = name[1]
                    field = deepcopy(self.base_fields[filter_name])
                    field.name = '%s|%s' % ('filter', filter_name)
                    #print "Fieldu %s jsem nasetil %s" % (field.name, field.value_from_datadict(self.data))
                    field.value = field.value_from_datadict(self.data)
                    
                    negation = (self.data.get('%s|%s' % ('negation', filter_name)) is not None)
                    field.negation = negation
                    
                    position_in_fields_sequence = self.data[name_str] # position is value of presention field
                    print 'position_in_fields_sequence = %s' % position_in_fields_sequence
                    fields_for_sort[position_in_fields_sequence] = field
            print "SORTED %s" % fields_for_sort.items()
            for pos, field in sorted(fields_for_sort.items()):  # adding fields in order according to presention field value
                self.fields[field.name] = field
        else:
            for field_name in self.default_fields_names:
                field = deepcopy(self.base_fields.get(field_name))
                field.name = '%s|%s' % ('filter', field_name)
                self.fields[field.name] = field
    
    def clean_field(self, name, field):
        value = field.value_from_datadict(self.data)#, self.files, self.add_prefix(name))
        try:
            value = field.clean(value)
            self.cleaned_data[name] = [field.negation, value]
            if hasattr(self, 'clean_%s' % name):
                value = getattr(self, 'clean_%s' % name)()
                self.cleaned_data[name] = [field.negation, value] # cleaned data of filterform is couple [negation, value]
        except ValidationError, e:
            self._errors[name] = e.messages
            if name in self.cleaned_data:
                del self.cleaned_data[name]

#class DomainsFilterForm2(FilterForm):
#    default_fields_names = ['owner', 'domain_name', 'crdate']
#    
#    domain_name = CharField(label=_('Domain name'))
#    crdate = DateIntervalField(label=_('Registration date'))
#    owner = CharField(label=_('Owner'))
#    registrar = CharField(label=_('Registrar'))
#    status1 = ChoiceField(choices=((1, u'Poraněn'), (2, u'Preživší'), (3, u'Mrtev'), (4, u'Nemrtvý')))
#    status2 = MultipleChoiceField(choices=((1, u'Poraněn'), (2, u'Preživší'), (3, u'Mrtev'), (4, u'Nemrtvý')))
#    email = EmailField(max_length=30)
#    expired = BooleanField()
#    valid = NullBooleanField() 
   
class RegistrarsFilterForm(FilterForm):
    default_fields_names = ['handle']
    
    name = CharField(label=_('Name'))
    handle = CharField(label=_('Handle'))
    ico = CharField(label=_('ICO'))
    vat = CharField(label=_('VAT'))
    crDate = DateIntervalField(label=_('Registration date'))
    upDate = DateIntervalField(label=_('Update date'))
    
class ContactsFilterForm(FilterForm):
    default_fields_names = ['handle', 'name']
    
    handle = CharField(label=_('Handle'))
    email = EmailField(label=_('Email'))
    registrar = CompoundFilterField(label=_('Selected registrar'), form_class=RegistrarsFilterForm)
    contact_type = MultipleChoiceField(label=_('Contact type'), choices=(('owner', _('Owner')), ('admin', _('Admin')), ('techadmin', _('techadmin')), ('temporary', _('Temporary'))))
    name = CharField(label=_('Name'))
    organisation = CharField(label=_('Organisation'))
    ssn = CharField(label=_('SSN'))
    vat = CharField(label=_('VAT'))
    crDate = DateIntervalField(label=_('Registration date'))
    upDate = DateIntervalField(label=_('Update date'))
#    vatt = RegexField(label=_('Vatt'))
    
class NSSetsFilterForm(FilterForm):
    default_fields_names = ['handle']
    
    handle = CharField(label=_('Handle'))
    ipAddr = CharField(label=_('IP address'))
    techAdmin = CompoundFilterField(label=_('Technical contact'), form_class=ContactsFilterForm)
    nsName = CharField(label=_('Nameserver name'))
    registrar = CompoundFilterField(label=_('Registrar'), form_class=RegistrarsFilterForm)
    createRegistrar = CompoundFilterField(label=_('Creation registrar'), form_class=RegistrarsFilterForm)
    updateRegistrar = CompoundFilterField(label=_('Update registrar'), form_class=RegistrarsFilterForm)
    crDate = DateIntervalField(label=_('Registration date'))
    upDate = DateIntervalField(label=_('Update date'))
    trDate = DateIntervalField(label=_('Transfer date'))
    
class DomainsFilterForm(FilterForm):
    default_fields_names = ['fqdn']
    
    fqdn = CharField(label=_('Domain name'))
    
    registrant = CompoundFilterField(label=_('Owner'), form_class=ContactsFilterForm)
    admin = CompoundFilterField(label=_('Admin'), form_class=ContactsFilterForm)
    nsset = CompoundFilterField(label=_('Nameserver set'), form_class=NSSetsFilterForm)
    registrar = CompoundFilterField(label=_('Registrar'), form_class=RegistrarsFilterForm)
    createRegistrar = CompoundFilterField(label=_('Creation registrar'), form_class=RegistrarsFilterForm)
    updateRegistrar = CompoundFilterField(label=_('Update registrar'), form_class=RegistrarsFilterForm)
    
    exDate = DateIntervalField(label=_('Expiry date'))
    valExDate = DateIntervalField(label=_('Validation date'))
    crDate = DateIntervalField(label=_('Registration date'))
    upDate = DateIntervalField(label=_('Update date'))
    trDate = DateIntervalField(label=_('Transfer date'))
    

class RequestsFilterForm(FilterForm):
    default_fields_names = ['requestType']
    
    requestType = ChoiceField(label=_('Request type'), choices=((1, u'Poraněn'), (2, u'Přeživší'), (3, u'Mrtev'), (4, u'Nemrtvý')))
    objectHandle = CharField(label=_('Object handle'))
    startDate = DateIntervalField(label=_('Received date'))
    result = ChoiceField(label=_('Result'), choices=((1, u'Poraněn'), (2, u'Preživší'), (3, u'Mrtev'), (4, u'Nemrtvý')))
    registrar = CompoundFilterField(label=_('Registrar'), form_class=RegistrarsFilterForm)
    svTRID = CharField(label=_('svTRID'))
    clTRID = CharField(label=_('clTRID'))
    
form_classes = (DomainsFilterForm, NSSetsFilterForm, ContactsFilterForm, RegistrarsFilterForm, RequestsFilterForm)
def get_filter_forms_javascript():
    'Javascript is cached in user session (must be there, bucause each user can have other forms, because of different permissions'
    if not cherrypy.session.has_key('filter_forms_javascript') or not config.caching_filter_form_javascript:
        output = u''
        for form in [form_class() for form_class in form_classes]:
            # Function for generating field of form
            output += form.layout(form).get_javascript_gener_field()
            # Function that generates empty form:
            output += "function getEmpty%s() {\n" % form.__class__.__name__
            #output += "return 'AHOJ';\n"
            output += "return '%s'\n" % escape_js_literal(unicode(form))
            output += "}\n"
        cherrypy.session['filter_forms_javascript'] = output
    return cherrypy.session['filter_forms_javascript']
   

#def valueToCorbaFilter(field):
#    
#    translation = {
#        CharField: field.value,
#        DateIntervalField: DateInterval(value[0], value[1]),
#    }
#    return translation[field.__class__]
#    }
#    