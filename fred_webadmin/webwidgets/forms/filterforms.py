#!/usr/bin/python
# -*- coding: utf-8 -*-
from copy import deepcopy

import simplejson
import cherrypy

from logging import debug, error
from fred_webadmin import config
from fred_webadmin.webwidgets.forms.forms import Form
from fred_webadmin.webwidgets.utils import (
    ErrorList, ValidationError)
from fred_webadmin.webwidgets.forms.fields import (
    CharField, ChoiceField, BooleanField, IntegerChoiceField,
    IntegerField) 
from fred_webadmin.webwidgets.forms.adiffields import (
    DateTimeIntervalField, CompoundFilterField, 
    CorbaEnumChoiceField, DateIntervalField)
from fred_webadmin.webwidgets.forms.filterformlayouts import (
    FilterTableFormLayout, UnionFilterFormLayout)
from fred_webadmin.translation import _
from fred_webadmin.webwidgets.utils import (
    SortedDict, ErrorDict, escape_js_literal)
from fred_webadmin.corbalazy import (
    CorbaLazyRequestIterStruct, ServerNotAvailableError)
from fred_webadmin.corba import ccReg, Registry
from fred_webadmin.mappings import f_urls
import fred_webadmin.webwidgets.forms.editforms as editforms
import fred_webadmin.webwidgets.forms.emptyvalue

__all__ = ['UnionFilterForm', 'RegistrarFilterForm', 'ObjectStateFilterForm', 
           'ObjectFilterForm', 'ContactFilterForm', 'NSSetFilterForm',
           'KeySetFilterForm', 'DomainFilterForm', 
           'ActionFilterForm', 'FilterFilterForm', 'PublicRequestFilterForm', 
           'InvoiceFilterForm', 'MailFilterForm', 'FileFilterForm',
           'LoggerFilterForm', 'BankStatementFilterForm', 'MessageFilterForm',
           'PropertyFilterForm',
           'get_filter_forms_javascript']

class UnionFilterForm(Form):
    ''' Form that contains more Filter Forms, data for this form is list of data
        for its Filter Forms. '''
    def __init__(self, data=None, data_cleaned=False, initial=None, 
                 layout_class=UnionFilterFormLayout, form_class=None, 
                 *content, **kwd):
        """ Form containting CompoundFilterForms (class FilterForms), between 
            them is logical OR. 
            Can be initilalized using data parametr data - normal form data, or 
            if data_cleaned=True, then data parametr is considered to be 
            cleaned_data (used when loaded from corba backend).
        """ 
        if not form_class:
            raise RuntimeError(
                "You have to specify form_class for UnionFilterForm!")

        if data:
            if not data_cleaned and data.has_key('json_data'):
                data = simplejson.loads(data['json_data'])
            else: 
                debug('data aren\'t json')

        self.form_class = form_class
        self.forms = []
        self.data_cleaned = data_cleaned
        super(UnionFilterForm, self).__init__(
            data, initial=initial, layout_class=layout_class, *content, **kwd)
        self.set_tattr(action = kwd.get('action') or self.get_default_url())
        self.media_files = ['/js/filtertable.js', 
                            '/js/scw.js', 
                            '/js/interval_fields.js', 
                            '/js/scwLanguages.js',
                            '/js/form_content.js',
                            '/service_actions.js',
                            '/filter_forms_javascript.js',
                            '/js/check_filter_forms_javascript.js',
                           ]
        # Submit on enter.
        self.onkeypress = 'if (event.keyCode == 13) {sendUnionForm(this);}'
    
    def set_fields_values(self):
        if not self.is_bound: # if not bound, then create one empty dictionary
            self.forms.append(self.form_class())
        else: # else create form for each value in 'data' list
            for form_data in self.data:
                debug('Creating form in unionu with data: %s' % form_data)
                debug('a that data are data_cleaned=%s' % self.data_cleaned)
                form = self.form_class(
                    form_data, data_cleaned=self.data_cleaned)
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
            return '%sfilter/' % f_urls[class_name[:-10].lower()]
        else:
            return ''
         
            
class FilterForm(Form):
    "Form for one coumpund filter (e.g. Domain Filter)"
    tattr_list = []
    default_fields_names = []
    name_postfix = 'FilterForm'
    nperm_names = ['read']
    
    def __init__(self, data=None, data_cleaned=False, files=None, 
                 auto_id='id_%s', prefix=None, initial=None, 
                 error_class=ErrorList, label_suffix=':', 
                 layout_class=FilterTableFormLayout, *content, **kwd):

        for field in self.base_fields.values():
            field.required = False
            field.negation = False
        
        self.data_cleaned = data_cleaned
        super(FilterForm, self).__init__(
            data, files, auto_id, prefix, initial, error_class, label_suffix, 
            layout_class, *content, **kwd)
        self.tag = None

    def _get_header_title(self):
        return _(self.__class__.__name__[:-len('FilterForm')] + 's')

    def get_key_time_field(self):
        """ Returns the filter form field used to jump to the previous/page 
            when displaying only the results for last day, month, year etc. 
            We increment this field's offset and re-submit the form to display 
            the results for the previous/next time interval.
        """
        return None
    
    def filter_base_fields(self):
        super(FilterForm, self).filter_base_fields()
        user = cherrypy.session.get('user', None)
        if user is None:
            self.default_fields_names = []
        else:
            self.default_fields_names = [field_name for field_name in \
                self.default_fields_names \
                if field_name in self.base_fields.keys()]
            
    def set_fields_values(self):
        pass # setting values is done in build_fields()
    
    def build_fields(self):
        """ Creates self.fields from given data or set default field (if not 
           is_bound).
            Data for filter forms are in following format: list of dictionaries, 
            where between each dictionary is OR. In dictionary, key is name of 
            field and value is value of that field. If field is compound filter, 
            then value is dictionary again.
        """
        # self.fields are deepcopied from self.base_fields (in BaseForm) 
        base_fields = self.base_fields 
        self.fields = SortedDict()

        fields_for_sort = []  
        if self.is_bound:
            if not self.data_cleaned:
                for name_str in self.data.keys():
                    name = name_str.split('|')
                    if len(name) >= 2 and name[0] == 'presention':
                        filter_name = name[1]
                        field = deepcopy(base_fields[filter_name])
                        if isinstance(field, CompoundFilterField):
                            field.parent_form = self
                        field.name = filter_name
                        field.value = field.value_from_datadict(self.data)
                        
                        negation = (self.data.get(
                            '%s|%s' % ('negation', filter_name)) is not None)
                        field.negation = negation
                        fields_for_sort.append(field)
            else: 
                # Data passed to t6he form in constructor are cleaned_data 
                # (e.g. from itertable.get_filter).
                for field_name, [neg, value] in self.data.items():
                    debug('field %s, setting value %s' % (field_name, value))
                    if not base_fields.get(field_name):
                        debug('field %s is in npermission -> skiping')
                        break 
                    # When field is in npermissions, it can still be here 
                    # if user loads saved filter -> 
                    field = deepcopy(base_fields[field_name])
                    if isinstance(field, CompoundFilterField):
                        field.parent_form = self
                    field.name = field_name
                    field.set_from_clean(value)
                    field.negation = neg
                    fields_for_sort.append(field)
        else:
            for field_name in self.default_fields_names:
                field = deepcopy(base_fields[field_name])
                field.name = field_name
                fields_for_sort.append(field)
        
        # adding fields in order according to field.order
        for pos, field in sorted(
                [[field.order, field] for field in fields_for_sort]):
            self.fields[field.name] = field
            field.owner_form = self
    
    def clean_field(self, name, field):
        try:
            value = field.clean()
            if field.is_empty():
                value = fred_webadmin.webwidgets.forms.emptyvalue.FilterFormEmptyValue()
            self.cleaned_data[name] = [field.negation, value]
            if hasattr(self, 'clean_%s' % name):
                value = getattr(self, 'clean_%s' % name)()
                # Cleaned data of filterform is couple [negation, value].
                self.cleaned_data[name] = [field.negation, value] 
        except ValidationError, e:
            self._errors[name] = e.messages
            if name in self.cleaned_data:
                del self.cleaned_data[name]


class RegistrarFilterForm(FilterForm):
    default_fields_names = ['Handle']
    
    Handle = CharField(label=_('Handle'))
    Name = CharField(label=_('Name'))
    Organization = CharField(label=_('Organization'))
    City = CharField(label=_('City'))
    CountryCode = CharField(label=_('Country'))
    ZoneFqdn = CharField(label=_('Zone fqdn'))
    GroupId = ChoiceField(
        label=_('Group'), 
        choices=CorbaLazyRequestIterStruct(
            'Admin', 'getGroupManager', 'getGroups', ['id', 'name'], 
            lambda groups: [g for g in groups if not g.cancelled]))

    
class ObjectStateFilterForm(FilterForm):
    default_field_names = ['StateId']

    StateId = ChoiceField(
        label=_('State Type'), 
        choices=CorbaLazyRequestIterStruct(
            'Admin', None, 'getObjectStatusDescList', 
            ['id', 'shortName'], None, config.lang[:2]))

    ValidFrom = DateTimeIntervalField(label=_('Valid from'))
    ValidTo = DateTimeIntervalField(label=_('Valid to'))


class ObjectFilterForm(FilterForm):
    default_fields_names = ['Handle']
    
    Handle = CharField(label=_('Handle'))
    AuthInfo = CharField(label=_('AuthInfo'))

    Registrar = CompoundFilterField(
        label=_('Registrar'), form_class=RegistrarFilterForm)
    CreateRegistrar = CompoundFilterField(
        label=_('Creation registrar'), form_class=RegistrarFilterForm)
    UpdateRegistrar = CompoundFilterField(
        label=_('Update registrar'), form_class=RegistrarFilterForm)
    
    CreateTime = DateTimeIntervalField(label=_('Registration date'))
    UpdateTime = DateTimeIntervalField(label=_('Update date'))
    TransferTime = DateTimeIntervalField(label=_('Transfer date'))
    DeleteTime = DateTimeIntervalField(label=_('Delete date'))

    ObjectState = CompoundFilterField(
        label=_('Object state'), form_class=ObjectStateFilterForm)

    
class ContactFilterForm(ObjectFilterForm):
    default_fields_names = ObjectFilterForm.default_fields_names + ['Name']
    
    Email = CharField(label=_('Email'))
    NotifyEmail = CharField(label=_('Notify email'))
    Name = CharField(label=_('Name'))
    Organization = CharField(label=_('Organization'))
    Ssn = CharField(label=_('Identification'))
    Vat = CharField(label=_('VAT'))
    PhoneNumber = CharField(label=_('Phone number'))
    
class NSSetFilterForm(ObjectFilterForm):
    TechContact = CompoundFilterField(
        label=_('Technical contact'), form_class=ContactFilterForm)
    HostIP = CharField(label=_('IP address'))
    HostFQDN = CharField(label=_('Nameserver name'))
    
    def clean(self):
        cleaned_data = super(NSSetFilterForm, self).clean()
        return cleaned_data

class KeySetFilterForm(ObjectFilterForm):
    TechContact = CompoundFilterField(
        label=_('Technical contact'), form_class=ContactFilterForm)
        
    
class DomainFilterForm(ObjectFilterForm):
    default_fields_names = ['Handle']
    
    Registrant = CompoundFilterField(
        label=_('Owner'), form_class=ContactFilterForm)
    AdminContact = CompoundFilterField(
        label=_('Admin'), form_class=ContactFilterForm, nperm='admins')
    TempContact = CompoundFilterField(
        label=_('Temp'), form_class=ContactFilterForm, nperm='temps')
    NSSet = CompoundFilterField(
        label=_('Nameserver set'), form_class=NSSetFilterForm)
    KeySet = CompoundFilterField(
        label=_('Key set'), form_class=KeySetFilterForm)    
    
    ExpirationDate = DateIntervalField(label=_('Expiry date'))
    OutZoneDate = DateIntervalField(label=_('OutZone date'))
    CancelDate = DateIntervalField(label=_('Cancel date'))

#    ValidationExpirationDate = DateIntervalField(label=_('Validation date'))


class ActionFilterForm(FilterForm):
    default_fields_names = ['SvTRID']
    
    Type = ChoiceField(
        label=_('Request type'), 
        choices=CorbaLazyRequestIterStruct(
            'Admin', None, 'getEPPActionTypeList', ['id', 'name'], None))
    Object = CompoundFilterField(label=_('Object'), form_class=ObjectFilterForm)
    RequestHandle = CharField(label=_('Requested Handle'))
    Time = DateTimeIntervalField(label=_('Received date'))
    Response = CorbaEnumChoiceField(
        label=_('Result'), corba_enum=Registry.EPPActionsFilterResultType)
    Registrar = CompoundFilterField(
        label=_('Registrar'), form_class=RegistrarFilterForm)
    SvTRID = CharField(label=_('SvTRID'))
    ClTRID = CharField(label=_('ClTRID'))

    def get_key_time_field(self):
        return self.base_fields['Time']


class PropertyFilterForm(FilterForm):
    default_fields_names = ['Name']
    Name = CharField(label=_('Name'))
    Value = CharField(label=_('Value'))
    OutputFlag = BooleanField(label=_('Output Flag'))

class ResultCodeFilterForm(FilterForm):
    default_fields_names = ['Name']
    Name = CharField(label=_('Name'))
    ResultCode = IntegerField(label=_('Result Code'))
    ServiceId = IntegerField(label=_('ServiceId'))

class LoggerFilterForm(FilterForm):
    def __init__(self, *args, **kwargs):
        super(LoggerFilterForm, self).__init__(*args, **kwargs)

    def _get_header_title(self):
        return _("Logged Actions")

    def get_key_time_field(self):
        return self.base_fields['TimeBegin']

    default_fields_names = ['ServiceType', 'TimeBegin', 'IsMonitoring']

    ServiceType = IntegerChoiceField(
        id="logger_service_type_id",
        label=_('Service type'),
        choices=CorbaLazyRequestIterStruct(
            'Logger', None, 'getServices', ['id', 'name'], None),
        onchange="filter_action_types();")
    SourceIp = CharField(label=_('Source IP'))
    UserName = CharField(label=_('Username'))
    RequestType = IntegerChoiceField(
        id="logger_action_type_id",
        label=_('Request type'), 
        choices=[],
        validate=False,
        onfocus="filter_action_types();")
    TimeBegin = DateTimeIntervalField(label=_('Begin time'))
    TimeEnd = DateTimeIntervalField(label=_('End time'))
    RequestPropertyValue = CompoundFilterField(
        label=_('Property'), form_class=PropertyFilterForm)
    ResultCode = CompoundFilterField(
        label=_('Result code'), form_class=ResultCodeFilterForm)
    IsMonitoring = BooleanField(label=_("Monitoring"))


class BankStatementFilterForm(FilterForm):
    def _get_header_title(self):
        return _("Payments")

    default_fields_names = ['Type']
    
    Type = IntegerChoiceField(label=_('Type'), choices=[
        (editforms.PAYMENT_UNASSIGNED,
            editforms.payment_map[editforms.PAYMENT_UNASSIGNED]),
        (editforms.PAYMENT_REGISTRAR, 
            editforms.payment_map[editforms.PAYMENT_REGISTRAR]),
        (editforms.PAYMENT_BANK, 
            editforms.payment_map[editforms.PAYMENT_BANK]), 
        (editforms.PAYMENT_ACCOUNTS, 
            editforms.payment_map[editforms.PAYMENT_ACCOUNTS]), 
        (editforms.PAYMENT_ACADEMIA,
            editforms.payment_map[editforms.PAYMENT_ACADEMIA]), 
        (editforms.PAYMENT_OTHER, 
            editforms.payment_map[editforms.PAYMENT_OTHER])])

    AccountDate = DateIntervalField(label=_('Account date'))
    
    AccountNumber = CharField(label=_('Account number'))
    BankCode = CharField(label=_('Bank code'))

    ConstSymb = CharField(label=_('Constant symbol'))
    VarSymb = CharField(label=_('Variable symbol'))

    CrTime = DateTimeIntervalField(label=_('Import time'))
    AccountMemo = CharField(label=_('Memo'))
    
    AccountId = ChoiceField(
        label=_('Destination account'), 
        choices=CorbaLazyRequestIterStruct(
            'Admin', None, 'getBankAccounts', ['id', 'name'], None))
     

class MessageFilterForm(FilterForm):
    default_fields_names = ['CrDate']
    CrDate = DateTimeIntervalField(label=_('Creation date'))
    ModDate = DateTimeIntervalField(label=_('Modification date'))
    Attempt = IntegerField(label=_('Attempts'))
    Status = ChoiceField(
        label=_('Status'), 
        choices=CorbaLazyRequestIterStruct(
            'Messages', None, 'getStatusList', ['id', 'name'], None))
    CommType = ChoiceField(
        label=_('Communication type'), 
        choices=CorbaLazyRequestIterStruct(
            'Messages', None, 'getCommTypeList', ['id', 'name'], None))
    MessageType = ChoiceField(
        label=_('Message type'), 
        choices=CorbaLazyRequestIterStruct(
            'Messages', None, 'getMessageTypeList', ['id', 'name'], None))
    SmsPhoneNumber = CharField(label=_('SMS phone number'))
    LetterAddrName = CharField(label=_('Letter address name'))
    MessageContact = CompoundFilterField(
        label=_('Message contact'), form_class=ContactFilterForm)

    
    
class FilterFilterForm(FilterForm):
    default_fields_names = ['Type']
    
    UserID = CharField(label=_('User name'))
    GroupID = CharField(label=_('Group name'))
    Type = ChoiceField(
        label=_('Result'), 
        choices=[(1, u'Poraněn'), (2, u'Preživší'), 
                 (3, u'Mrtev'), (4, u'Nemrtvý')])


class PublicRequestFilterForm(FilterForm):
    default_fields_names = ['Id']
    
    Id = IntegerField(label=_('ID'))
    Type = CorbaEnumChoiceField(
        label=_('Type'), corba_enum=Registry.PublicRequest.Type)
    Status = CorbaEnumChoiceField(
        label=_('Status'), corba_enum=Registry.PublicRequest.Status)
    CreateTime = DateTimeIntervalField(label=_('Create time'))
    ResolveTime = DateTimeIntervalField(label=_('Resolve time'))
    Reason = CharField(label=_('Reason'))
    EmailToAnswer = CharField(label=_('Email to answer'))
    Object = CompoundFilterField(label=_('Object'), form_class=ObjectFilterForm)
    EppAction = CompoundFilterField(
        label=_('Action'), form_class=ActionFilterForm)


class FileFilterForm(FilterForm):
    default_fields_names = ['Type']
    
    Name = CharField(label=_('Name'))
    Path = CharField(label=_('Path'))
    MimeType = CharField(label=_('Mime type'))
    CreateTime = DateTimeIntervalField(label=_('Create time'))
    Type = ChoiceField(
        label=_('Type'), 
        choices=CorbaLazyRequestIterStruct(
            'FileManager', None, 'getTypeEnum', ['id', 'name'], None))


class InvoiceFilterForm(FilterForm):
    default_fields_names = ['Type']
    
    Type = CorbaEnumChoiceField(
        label=_('Type'), corba_enum=Registry.Invoicing.InvoiceType)
    Number = CharField(label=_('Number'))
    CreateTime = DateTimeIntervalField(label=_('Create time'))
    TaxDate = DateIntervalField(label=_('Tax date'))
    Registrar = CompoundFilterField(
        label=_('Registrar'), form_class=RegistrarFilterForm)
    Object = CompoundFilterField(label=_('Object'), form_class=ObjectFilterForm)
    File = CompoundFilterField(label=_('File'), form_class=FileFilterForm)


class MailFilterForm(FilterForm):
    default_fields_names = ['CreateTime', 'Type']
    
    Type = ChoiceField(
        label=_('Type'), 
        choices=CorbaLazyRequestIterStruct(
            'Mailer', None, 'getMailTypes', ['id', 'name'], None))
    Handle = CharField(label=_('Handle'))
    CreateTime = DateTimeIntervalField(label=_('Create time'))
    ModifyTime = DateTimeIntervalField(label=_('Modify time'))
    # docasny, az bude v corba tak smazat
    Status = IntegerField(label=_('Status'))
    Attempt = IntegerField(label=_('Attempt'))
    Message = CharField(label=_('Message'))
    Attachment = CompoundFilterField(
        label=_('Attachment'), form_class=FileFilterForm)

    def get_key_time_field(self):
        return self.base_fields['CreateTime']

      
# This has to be a list and not a tuple, because ADIF can remove e.g. logger
# filter during login when logging is disabled.
form_classes = [DomainFilterForm, 
                NSSetFilterForm, 
                KeySetFilterForm,                 
                ObjectFilterForm, 
                ContactFilterForm, 
                RegistrarFilterForm, 
                ActionFilterForm,
                FilterFilterForm,
                PublicRequestFilterForm,
                FileFilterForm,
                InvoiceFilterForm,
                MailFilterForm,
                ObjectStateFilterForm,
                LoggerFilterForm,
                BankStatementFilterForm,
                MessageFilterForm,
                PropertyFilterForm,
                ResultCodeFilterForm]

def get_filter_forms_javascript(filter_form_classes):
    """ Javascript is cached in user session (must be there, beucause each user 
        can have other forms, because of different permissions. 
    """
    output = u''
    all_fields_dict = {}
#    import ipdb; ipdb.set_trace()
    for form_class in filter_form_classes: 
        form = form_class()
        # Function for generating field of form
        try:
            output_part, fields_js_dict = form.layout_class(form).get_javascript_gener_field()
        except ServerNotAvailableError:
            # We need to connect to a CORBA server to get field values for some
            # filters. If the connection attempt fails, skip the filter.
            # TODO(tom): Should we really just skip it?
            error("Could not get filter for object %s!" % form_class)
            continue
        output += output_part
        
        all_fields_dict[form.get_object_name()] = fields_js_dict
        
        # Function that generates empty form:
        output += "function getEmpty%s() {\n" % form.__class__.__name__
        output += "    return '%s'\n" % escape_js_literal(unicode(form))
        output += "}\n"
    output += u'allFieldsDict = %s' % (simplejson.dumps(all_fields_dict) + u'\n')
    return output

def get_service_actions_javascript(logd):
    types = [item.id for item in logd.getServices()]
    js = ""
    result = {}
    for t in types:
        actions = logd.getRequestTypesByService(t)
        result[t] = [[a.id, a.name] for a in actions]
    js = """function get_actions() { var res=%s; return res;}""" % result
    return js
