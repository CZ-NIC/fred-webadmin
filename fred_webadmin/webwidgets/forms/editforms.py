#!/usr/bin/python
# -*- coding: utf-8 -*-

from logging import debug

from fred_webadmin import config

from forms import Form
from fields import *
from adiffields import *
from formsets import BaseFormSet

from fred_webadmin.translation import _
from fred_webadmin.corbalazy import CorbaLazyRequest, CorbaLazyRequestIterStruct
from editformlayouts import EditFormLayout

class EditForm(Form):
    "Base class for all forms used for editing objects"
    nperm_name = 'change'
    # XXX: Tak tohle se bude muset predelat, protoze pro editform nelze
    # XXX: jednoduse spustit filter_base_fields(), protoze pak se odesila
    # XXX: cely objekt a field, ktery neni pritomen by se nastavil na PRAZDNY RETEZEC!!!
    # XXX: Takze bud bude nutne to tam nejak dodelat, aby se ty schovany kopirovaly z initial, nebo tak ne.
    # XXX: Dale je take mozna problem v pridanych fieldech
    name_postfix = 'EditForm'
    
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':', layout_class=EditFormLayout, *content, **kwd):
        super(EditForm, self).__init__(data, files, auto_id, prefix, initial, error_class, label_suffix, layout_class=EditFormLayout, *content, **kwd)
        
    
    def filter_base_fields(self):
        pass # viz. XXX: poznamky nahore
    
    def set_fields_values(self):
        super(EditForm, self).set_fields_values()
        for field in self.fields.values():
            initial_value = self.initial.get(field.name_orig, field.initial)
            if not isinstance(field, FormSetField):
                if isinstance(field, BooleanField): # checkbox
                    if initial_value:
                        field.title = 'checked'
                    else:
                        field.title = 'unchecked'
                else: # usual field
                    field.title = initial_value
                

class AccessEditForm(EditForm):
    password = CharField(label=_('Password'))
    md5Cert = CharField(label=_('MD5 of cert.'))

class RegistrarEditForm(EditForm):
    id = HiddenDecimalField()
    handle = CharField(label=_('Handle')) # registrar identification
    name = CharField(label=_('Name'), required=False) # registrar name
    organization = CharField(label=_('Organization'), required=False) # organization name
    street1 = CharField(label=_('Street1'), required=False) # address part 1
    street2 = CharField(label=_('Street2'), required=False) # address part 2
    street3 = CharField(label=_('Street3'), required=False) # address part 3
    city = CharField(label=_('City'), required=False) # city of registrar headquaters
    stateorprovince = CharField(label=_('State'), required=False) # address part
    postalcode = CharField(label=_('ZIP'), required=False) # address part
    country = ChoiceField(label=_('Country'), choices=CorbaLazyRequestIterStruct('Admin', 'getCountryDescList', ['cc', 'name']), initial=CorbaLazyRequest('Admin', 'getDefaultCountry'), required=False) # country code
#    country = ChoiceField(label=_('Country'), choices=CorbaLazyRequestIterStruct('Admin', 'getCountryDescList', ['cc', 'name'], required=False), initial='CZ') # country code    
    
    ico = CharField(label=_('ICO'), required=False)
    dic = CharField(label=_('DIC'), required=False)
    varSymb = CharField(label=_('Var. Symbol'), required=False)
    vat = BooleanField(label=_('DPH'), required=False)

    telephone = CharField(label=_('Telephone'), required=False) # phne number
    fax = CharField(label=_('Fax'), required=False) # fax number
    email = CharField(label=_('Email'), required=False) # contact email
    url = CharField(label=_('URL'), required=False) # URL
    hidden = BooleanField(label=_('Hidden in PIF'), required=False) # hidden in PIF
    #access = EPPAccessSeq # list of epp access data
    access = FormSetField(label=_('Authentication'), form_class=AccessEditForm, can_delete=True)
    
    
