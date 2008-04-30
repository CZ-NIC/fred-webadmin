#!/usr/bin/python
# -*- coding: utf-8 -*-

from copy import deepcopy
#def deepcopy(a): 
#    return a
import cherrypy
import simplejson
from logging import debug

from fred_webadmin import config
from forms import Form, SortedDictFromList
from fields import *
from adiffields import *
from formlayouts import FilterTableFormLayout, UnionFilterFormLayout
from fred_webadmin import config
from fred_webadmin.translation import _
from utils import SortedDict, ErrorDict, escape_js_literal
from fred_webadmin.corbalazy import CorbaLazyRequest, CorbaLazyRequest1V2L
from fred_webadmin.corba import ccReg

#__all__ = ['LoginForm', 'FilterForm']

class FilterFormEmptyValue(object):
    '''Class used in clean method of Field as empty value (if field.is_emtpy()=True, than clean vill return instance of this object'''
    pass

class LoginForm(Form):
    corba_server = ChoiceField(choices=[(str(i), ior[0]) for i, ior in enumerate(config.iors)], label=_("Server"))
    login = CharField(max_length=30, label=_('Username'))#, initial=_(u'ohíňěček ťůříšekňú'))
    password = PasswordField(max_length=30)
    next = HiddenField(initial='/')
    media_files = 'form_files.js'

class UnionFilterForm(Form):
    'Form that contains more Filter Forms, data for this form is list of data for its Filter Forms'
    def __init__(self, data=None, data_cleaned=False, initial=None, layout=UnionFilterFormLayout, form_class=None, *content, **kwd):
        '''
        Form containting CompoundFilterForms (class FilterForms), between them is logical OR.
        Can be initilalize using data parametr data - normal form data, or if data_cleaned=True, then data parametr is considered
        to be cleaned_data (used when loaded from corba backend)
        ''' 
        debug('CREATING UNIONFORM')
        if not form_class:
            raise RuntimeError('You have to specify form_class for UnionFilterForm!')

        if data:
            debug('data:%s' % data)
            if not data_cleaned and data.has_key('json_data'):
                debug('data are json, so they are going to be transformed')
                data = simplejson.loads(data['json_data'])
            else: debug('data aren\'t json')

        self.form_class = form_class
        self.forms = []
        self.data_cleaned = data_cleaned
        super(UnionFilterForm, self).__init__(data, initial=initial, layout=layout, *content, **kwd)
        self.set_tattr(action = kwd.get('action') or self.get_default_url())
        self.media_files = ['/js/filtertable.js', 
                            #'/js/MochiKit/MochiKit.js', 
                            '/js/scw.js', 
                            '/js/interval_fields.js', 
                            '/js/scwLanguages.js',
                            '/js/form_content.js',
                            '/filter_forms_javascript.js'
                           ]
        #self.onsubmit = '''alert('submituji');sendUnionForm(this); return false;'''
        #self.onsubmit = '''alert('submituju'); false;'''
        self.onkeypress = 'if (event.keyCode == 13) {sendUnionForm(this);}' # submit on enter
    
    def set_fields_values(self):
        if not self.is_bound: # if not bound, then create one empty dictionary
            self.forms.append(self.form_class())
        else: # else create form for each value in 'data' list
            for form_data in self.data:
                debug('Creating form in unionu with data: %s' % form_data)
                debug('a that data are data_cleaned=%s' % self.data_cleaned)
                form = self.form_class(form_data, data_cleaned=self.data_cleaned)
                self.forms.append(form)
    
        
    def is_empty(self, exceptions=None):
        for form in self.forms:
            if form.is_empty(exceptions):
                return False
        return True
    
    def full_clean(self):
        debug('FULL CLEAN IN UNIONFROM')
        self._errors = ErrorDict()
        if not self.is_bound: # Stop further processing.
            return
        self.cleaned_data = []
        
        for form in self.forms:
            debug('SUBFORM %s' % repr(form))
            debug('SUBFORM.errors %s' % repr(form.errors))
            self._errors.update(form.errors)
            if hasattr(form, 'cleaned_data'):
                self.cleaned_data.append(form.cleaned_data)
        
        if self._errors:
            delattr(self, 'cleaned_data')
            
    def get_default_url(self):
        '''
        Returns url for snadard path /OBJECTs/filter where OBJECT taken from self.form_class name OBJECTsFilterForm.
        If class name is not in format, than returns ''.
        '''
        class_name = self.form_class.__name__ 
        if class_name.endswith('FilterForm'):
            return '/%s/filter/' % class_name[:-10].lower()
        else:
            return ''
         
            
class FilterForm(Form):
    "Form for one coumpund filter (e.g. Domains Filter)"
    tattr_list = []
    default_fields_names = []
    def __init__(self, data=None, data_cleaned=False, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':', layout=FilterTableFormLayout,
                 is_nested = False,
                 *content, **kwd):
        
        for field in self.base_fields.values():
            field.required = False
            field.negation = False
        
        self.is_nested = is_nested
        self.data_cleaned = data_cleaned
        self.layout = layout
        self.filter_base_fields()
        super(FilterForm, self).__init__(data, files, auto_id, prefix, initial, error_class, label_suffix, layout, *content, **kwd)
        self.tag = None
    
    @classmethod
    def get_object_name(cls):
        return cls.__name__[:-len('sFilterForm')].lower()

    def set_fields_values(self):
        pass # setting values is done in build_fields()
    
    def filter_base_fields(self):
        "Filters base fields against user negative permissions, so if user has nperm on field we delete it from base_fields (only in istance of FilterForm class)"
        user = cherrypy.session.get('user', None)
        #import pdb; pdb.set_trace()
        object_name = self.get_object_name()
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
        base_fields = self.base_fields # self.fields are deepcopied from self.base_fields (in BaseForm) 
        self.fields = SortedDict()

        fields_for_sort = []  
        if self.is_bound:
            debug('DATA %s' % self.data)
            debug("SELF>data_cleaned %s" % self.data_cleaned)
            if not self.data_cleaned:
                for name_str in self.data.keys():
                    name = name_str.split('|')
                    if len(name) >= 2 and name[0] == 'presention':
                        filter_name = name[1]
                        field = deepcopy(base_fields[filter_name])
                        if isinstance(field, CompoundFilterField):
                            field.parent_form = self
                        field.name = '%s|%s' % ('filter', filter_name)
                        field.value = field.value_from_datadict(self.data)
                        
                        negation = (self.data.get('%s|%s' % ('negation', filter_name)) is not None)
                        field.negation = negation
                        fields_for_sort.append(field)
            else: # data passed to form in constructor are cleaned_data (e.g. from itertable.get_filter)
                for name_str, [neg, value] in self.data.items():
                    filter_name = name_str.split('|')[1]
                    debug('field %s, setting value %s' % (filter_name, value))
                    field = deepcopy(base_fields[filter_name])
                    if isinstance(field, CompoundFilterField):
                        field.parent_form = self
                    field.name = name_str
                    field.set_from_clean(value)
                    field.negation = neg
                    fields_for_sort.append(field)
        else:
            for field_name in self.default_fields_names:
                field = deepcopy(base_fields[field_name])
                field.name = '%s|%s' % ('filter', field_name)
                fields_for_sort.append(field)
        
        # adding fields in order according to field.order
        for pos, field in sorted([[field.order, field] for field in fields_for_sort]):  
            self.fields[field.name] = field
        debug("RESULTED FIELDS %s" % self.fields.items())
    
    def clean_field(self, name, field):
        try:
            value = field.clean()
            if field.is_empty():
                value = FilterFormEmptyValue()
            self.cleaned_data[name] = [field.negation, value]
            if hasattr(self, 'clean_%s' % name):
                value = getattr(self, 'clean_%s' % name)()
                self.cleaned_data[name] = [field.negation, value] # cleaned data of filterform is couple [negation, value]
        except ValidationError, e:
            self._errors[name] = e.messages
            if name in self.cleaned_data:
                del self.cleaned_data[name]

#    def get_fields_for_layout(self, parent_prefix_composed_name, parent_prefix_label):
#        fields = []
#        
#        for field in self.fields.values():
#            new_label = '%s.%s' % (parent_prefix_label, field.label)
#            new_composed_name = '%s.%s' % (parent_prefix_composed_name, field.composed_name)
#            
#            if not isinstance(field,  CompoundFilterField):
#                field.label = new_label
#                field.composed_name = new_composed_name 
#                fields.append(field)
#            else:
#                fields.extend(field.form.get_fields_for_layout(new_label, new_composed_name))
#        
#        return fields
#        
#    def get_non_fields_errors_for_layout(self):
#        non_fields_errors = self.non_field_errors()
#        
#        for field in self.fields.values():
#            if isinstance(field,  CompoundFilterField):
#                non_fields_errors.extend(field.form.get_non_fields_errors_for_layout)
#        return non_fields_errors

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
#    cas = TimeField(label=('cas vyrazeni'))
#    datumpropadnuti = SplitDateTimeField(label=_('Datum propadnuti'))
#    casprejmenovani = SplitTimeField(label=_('cas prejmenovani'))
#    datum_umrti = SplitDateSplitTimeField(label=_('datum umrti'))
#    doba_zmrtvychvstani = DateTimeIntervalField(label=_('doba zmrtvychvstani'))
   
class RegistrarsFilterForm(FilterForm):
    default_fields_names = ['Handle']
    
    Name = CharField(label=_('Name'))
    Handle = CharField(label=_('Handle'))
    Organization = CharField(label=_('Organization'))
    City = CharField(label=_('City'))
    Country = CharField(label=_('Country'))
    
#    ico = CharField(label=_('ICO'))
#    vat = CharField(label=_('VAT'))
#    crDate = DateIntervalField(label=_('Registration date'))
#    upDate = DateIntervalField(label=_('Update date'))
    
class ObjectsFilterForm(FilterForm):
    default_fields_names = ['Handle']
    
    Handle = CharField(label=_('Handle'))
    AuthInfo = CharField(label=_('AuthInfo'))

    Registrar = CompoundFilterField(label=_('Registrar'), form_class=RegistrarsFilterForm)
    CreateRegistrar = CompoundFilterField(label=_('Creation registrar'), form_class=RegistrarsFilterForm)
    UpdateRegistrar = CompoundFilterField(label=_('Update registrar'), form_class=RegistrarsFilterForm)
    
    CreateTime = DateTimeIntervalField(label=_('Registration date'))
    UpdateTime = DateTimeIntervalField(label=_('Update date'))
    TransferTime = DateTimeIntervalField(label=_('Transfer date'))
    DeleteTime = DateTimeIntervalField(label=_('Delete date'))
    
class ContactsFilterForm(ObjectsFilterForm):
    default_fields_names = ObjectsFilterForm.default_fields_names + ['Name']
    
    Email = EmailField(label=_('Email'))
    NotifyEmail = EmailField(label=_('Notify email'))
#    contact_type = MultipleChoiceField(label=_('Contact type'), choices=(('owner', _('Owner')), ('admin', _('Admin')), ('techadmin', _('techadmin')), ('temporary', _('Temporary'))))
    Name = CharField(label=_('Name'))
    Organization = CharField(label=_('Organization'))
    Ssn = CharField(label=_('Identification'))
    Vat = CharField(label=_('VAT'))
    
class NSSetsFilterForm(ObjectsFilterForm):
    TechContact = CompoundFilterField(label=_('Technical contact'), form_class=ContactsFilterForm)
    HostIP = CharField(label=_('IP address'))
    HostFQDN = CharField(label=_('Nameserver name'))
    #HostFQDN1 = CharField(label=_('Nameserver name 1'))
    #HostFQDN2 = CharField(label=_('Nameserver name 2'))
    
    def clean(self):
        cleaned_data = super(NSSetsFilterForm, self).clean()
        return cleaned_data
        
    
class DomainsFilterForm(ObjectsFilterForm):
    default_fields_names = ['Handle']
    
#    fqdn = CharField(label=_('Domain name'))
    Registrant = CompoundFilterField(label=_('Owner'), form_class=ContactsFilterForm)
    AdminContact = CompoundFilterField(label=_('Admin'), form_class=ContactsFilterForm)
    TempContact = CompoundFilterField(label=_('Temp'), form_class=ContactsFilterForm)
    NSSet = CompoundFilterField(label=_('Nameserver set'), form_class=NSSetsFilterForm)
    
    ExpirationDate = DateIntervalField(label=_('Expiry date'))
    ValidationExpirationDate = DateIntervalField(label=_('Validation date'))


class ActionsFilterForm(FilterForm):
    default_fields_names = ['SvTRID']
    
    #Type = MultipleChoiceField(label=_('Request type'), choices=((1, u'Poraněn'), (2, u'Přeživší'), (3, u'Mrtev'), (4, u'Nemrtvý')))
    Type = ChoiceField(label=_('Request type'), choices=CorbaLazyRequest1V2L('Admin', 'getEPPActionTypeList'))
    Object = CompoundFilterField(label=_('Object'), form_class=ObjectsFilterForm)
    Time = DateTimeIntervalField(label=_('Received date'))
    Response = CorbaEnumChoiceField(label=_('Result'), corba_enum=ccReg.EPPActionsFilter.ResultType)
    Registrar = CompoundFilterField(label=_('Registrar'), form_class=RegistrarsFilterForm)
    SvTRID = CharField(label=_('SvTRID'))
    ClTRID = CharField(label=_('ClTRID'))
    

class FiltersFilterForm(FilterForm):
    default_fields_names = ['Type']
    
    UserID = CharField(label=_('User name'))
    GroupID = CharField(label=_('Group name'))
    Type = ChoiceField(label=_('Result'), choices=((1, u'Poraněn'), (2, u'Preživší'), (3, u'Mrtev'), (4, u'Nemrtvý')))
    

form_classes = (DomainsFilterForm, 
                NSSetsFilterForm, 
                ObjectsFilterForm, 
                ContactsFilterForm, 
                RegistrarsFilterForm, 
                ActionsFilterForm,
                FiltersFilterForm)

def get_filter_forms_javascript():
    'Javascript is cached in user session (must be there, bucause each user can have other forms, because of different permissions'
    if not cherrypy.session.has_key('filter_forms_javascript') or not config.caching_filter_form_javascript:
        output = u''
        all_fields_dict = {}
        for form_class in form_classes: 
            form = form_class()
            # Function for generating field of form
            output_part, fields_js_dict = form.layout(form).get_javascript_gener_field()
            output += output_part
            
            all_fields_dict[form.get_object_name()] = fields_js_dict
            
            # Function that generates empty form:
            output += "function getEmpty%s() {\n" % form.__class__.__name__
            output += "    return '%s'\n" % escape_js_literal(unicode(form))
            output += "}\n"
        output += u'allFieldsDict = %s' % (simplejson.dumps(all_fields_dict) + u'\n')
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