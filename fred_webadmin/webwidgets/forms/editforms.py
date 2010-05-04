#!/usr/bin/python
# -*- coding: utf-8 -*-
import cherrypy
from logging import debug

from fred_webadmin import config

from forms import Form
from fields import *
from adiffields import *
from formsets import BaseFormSet

import fred_webadmin.controller.adiferrors as adiferrors

from fred_webadmin.translation import _
from fred_webadmin.corbalazy import CorbaLazyRequest, CorbaLazyRequestIterStruct
from editformlayouts import (
    EditFormLayout, RegistrarEditFormLayout)
from formlayouts import (
    NestedFieldsetFormSectionLayout, 
    SimpleFieldsetFormSectionLayout, DivFormSectionLayout)
from fred_webadmin.webwidgets.forms.formsetlayouts import DivFormSetLayout

from fred_webadmin.utils import get_current_url
import fred_webadmin.mappings as mappings
import fred_webadmin.utils

from fred_webadmin.corba import ccReg, Registry
import fred_webadmin.corbarecoder as recoder

PAYMENT_UNASSIGNED = 1
PAYMENT_REGISTRAR = 2
PAYMENT_BANK = 3
PAYMENT_ACCOUNTS = 4
PAYMENT_ACADEMIA = 5
PAYMENT_OTHER = 6

payment_map = dict([(PAYMENT_UNASSIGNED, u'Not assigned'),
(PAYMENT_REGISTRAR, u'From/to registrar'),
(PAYMENT_BANK, u"From/to bank"), 
(PAYMENT_ACCOUNTS, u'Between our own accounts'), 
(PAYMENT_ACADEMIA, u'Related to Academia'), 
(PAYMENT_OTHER, u'Other transfers')])


class UpdateFailedError(adiferrors.AdifError):
    pass


class EditForm(Form):
    "Base class for all forms used for editing objects"
    nperm_names = ['read', 'change']
    # XXX: Tak tohle se bude muset predelat, protoze pro editform nelze
    # XXX: jednoduse spustit filter_base_fields(), protoze pak se odesila
    # XXX: cely objekt a field, ktery neni pritomen by se nastavil na PRAZDNY RETEZEC!!!
    # XXX: Takze bud bude nutne to tam nejak dodelat, aby se ty schovany kopirovaly z initial, nebo tak ne.
    # XXX: Dale je take mozna problem v pridanych fieldech
    name_postfix = 'EditForm'
    
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':', 
                 layout_class=EditFormLayout, *content, **kwd):
        super(EditForm, self).__init__(
            data, files, auto_id, prefix, initial, error_class, label_suffix, 
            layout_class, *content, **kwd)
        self.media_files = ['/js/scw.js', 
                            '/js/scwLanguages.js',
                            '/js/publicrequests.js']
    
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

    def fire_actions(self, *args, **kwargs): 
        """ To be called after the form is submitted. Calls field.fire_actions
            for each field in the form.
        """
        for field in self.fields.values():
            field.fire_actions(*args, **kwargs)
                

class AccessEditForm(EditForm):
    password = CharField(label=_('Password'))
    md5Cert = CharField(label=_('MD5 of cert.'))


class ZoneEditForm(EditForm):
    id = HiddenIntegerField(initial=0)

    name = CharField(label=_('Name'))
    fromDate = DateField(label=_('From'))
    toDate = DateField(label=_('To'), required=False)

    def clean(self):
        """ Check that To' date is bigger than 'From' date. """
        toDate = self.fields['toDate'].value
        fromDate = self.fields['fromDate'].value
        if fromDate and toDate:
            if toDate < fromDate:
                raise ValidationError(
                    "'To' date must be bigger than 'From' date.")
        if 'fromDate' in self.changed_data:
            if fromDate < datetime.date.today().isoformat():
                raise ValidationError("'From' date must be in future.")
        return self.cleaned_data


class SingleGroupEditForm(EditForm):
    id = ChoiceField(
        label=_('name'), 
        choices=CorbaLazyRequestIterStruct(
            'Admin', 'getGroupManager', 'getGroups', ['id', 'name']),
        required=False)

    def fire_actions(self, reg_id, *args, **kwargs): 
        mgr = cherrypy.session['Admin'].getGroupManager()
        group_id = self.fields['id'].value
        if not group_id:
            return
        else:
            group_id = int(group_id)
        try:
            if "id" in self.changed_data:
                mgr.addRegistrarToGroup(reg_id, group_id)
            elif 'DELETE' in self.changed_data:
                mgr.removeRegistrarFromGroup(reg_id, group_id)
        except Registry.Registrar.InvalidValue:
            raise UpdateFailedError(
                "Invalid registrar group value provided")


class CertificationEditForm(EditForm):
    toDate = DateField(label=_("To"))
    score = IntegerField(label=_("Score"))
    evaluation_file_id = FileField(label=_("Evaluation"), type="file")


class RegistrarEditForm(EditForm):
    def __init__(self, *args, **kwargs):
        super(RegistrarEditForm, self).__init__(
            layout_class=RegistrarEditFormLayout,
            enctype="multipart/form-data", *args, **kwargs)
    
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
    countryCode = ChoiceField(
        label=_('Country'), 
        choices=CorbaLazyRequestIterStruct(
            'Admin', None, 'getCountryDescList', ['cc', 'name']), 
        initial=CorbaLazyRequest('Admin', None, 'getDefaultCountry'), 
        required=False) # country code
    
    ico = CharField(label=_('ICO'), required=False)
    dic = CharField(label=_('DIC'), required=False)
    varSymb = CharField(label=_('Var. Symbol'), required=False)
    vat = BooleanField(label=_('DPH'), required=False)

    telephone = CharField(label=_('Telephone'), required=False) # phne number
    fax = CharField(label=_('Fax'), required=False) # fax number
    email = CharField(label=_('Email'), required=False) # contact email
    url = CharField(label=_('URL'), required=False) # URL
    hidden = BooleanField(label=_('System registrar'), required=False) # System registrar
    
    access = FormSetField(
        label=_('Authentication'), form_class=AccessEditForm, can_delete=True,
        formset_layout=DivFormSetLayout)
    zones = FormSetField(
        label=_('Zones'), form_class=ZoneEditForm, 
        can_delete=False, formset_layout=DivFormSetLayout)
    groups = FormSetField(
        label=_('Groups'), form_class=SingleGroupEditForm, can_delete=False)
    certifications = FormSetField(
        label=_('Certifications'), form_class=CertificationEditForm, 
        can_delete=False)

    sections = (
        (_("Registrar data"), (
            "handle", "name", "organization", 'street1', 'street2', 
            'street3', 'city', 'postalcode', 'stateorprovince', 'countryCode',
            "postalCode", "ico", "dic", "varSymb", "vat", "telephone", "fax",
            "email", "url", "id"),
            SimpleFieldsetFormSectionLayout),
        (_("Authentication"), ("access"), NestedFieldsetFormSectionLayout),
        (_("Zones"), ("zones"), NestedFieldsetFormSectionLayout),
        (_("Groups"), ("groups"), NestedFieldsetFormSectionLayout),
        (_("Certifications"), ("certifications"), NestedFieldsetFormSectionLayout),
    )

    def fire_actions(self, *args, **kwargs):
        try:
            reg = kwargs["updated_registrar"]
        except KeyError:
            raise RuntimeError(
                "RegistrarDataEditForm: Failed to fetch "
                "updated registrar from kwargs.")
        try:
            reg_id = fred_webadmin.utils.get_corba_session().updateRegistrar(reg)
        except ccReg.Admin.UpdateFailed, e:
            raise UpdateFailedError(
                "Updating registrar failed. Perhaps you tried to "
                "create a registrar with an already used handle?")
        # Set created/updated registrar id to result (it is used in ADIF
        # registrar page).
        kwargs["result"]['reg_id'] = reg_id
        # Fire actions for groups.
        self.fields["groups"].fire_actions(reg_id=reg_id, *args, **kwargs)
   

class BankStatementPairingEditForm(EditForm):
    type = IntegerChoiceField(
        label=_('Type'), choices=[
            (PAYMENT_REGISTRAR, payment_map[PAYMENT_REGISTRAR]),
            (PAYMENT_BANK, payment_map[PAYMENT_BANK]), 
            (PAYMENT_ACCOUNTS, payment_map[PAYMENT_ACCOUNTS]), 
            (PAYMENT_ACADEMIA, payment_map[PAYMENT_ACADEMIA]), 
            (PAYMENT_OTHER, payment_map[PAYMENT_OTHER])],
        onchange="disableRegistrarHandle();")#, onload="disableRegistrarHandle();")
    handle = CharField(
        label=_('Pair with Registrar Handle'), name="registrar_handle_input")
    id = HiddenIntegerField()


class RegistrarGroupsEditForm(EditForm):
    name = CharField(label=_("Group name"))
    id = HiddenIntegerField()

    def fire_actions(self, *args, **kwargs):
        mgr = cherrypy.session['Admin'].getGroupManager()
        group_id = self.fields['id'].value
        group_name = recoder.u2c(self.fields['name'].value)
        if not group_id:
            if ("name" in self.changed_data):
                mgr.createGroup(group_name)
        else:
            group_id = int(group_id)
            if 'DELETE' in self.changed_data:
                mgr.deleteGroup(group_id)
            elif 'group_name' in self.changed_data:
                mgr.updateGroup(group_id, group_name)


class GroupManagerEditForm(EditForm):
    groups = FormSetField(
        label=_('Registrar groups'), form_class=RegistrarGroupsEditForm, 
        can_delete=True)


form_classes = [
    AccessEditForm, RegistrarEditForm, BankStatementPairingEditForm, 
    ZoneEditForm, RegistrarGroupsEditForm, SingleGroupEditForm]
