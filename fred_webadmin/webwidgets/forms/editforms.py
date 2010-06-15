#!/usr/bin/python
# -*- coding: utf-8 -*-
import cherrypy
from logging import debug, error

from fred_webadmin.webwidgets.forms.forms import Form
from fields import *
from fred_webadmin.webwidgets.forms.adiffields import *
from fred_webadmin.webwidgets.forms.formsets import BaseFormSet
from datetime import date

import fred_webadmin.controller.adiferrors as adiferrors

from fred_webadmin.translation import _
from fred_webadmin.corbalazy import CorbaLazyRequest, CorbaLazyRequestIterStruct
from fred_webadmin.webwidgets.forms.editformlayouts import (
    EditFormLayout, RegistrarEditFormLayout)
from fred_webadmin.webwidgets.forms.formlayouts import (
    HideableNestedFieldsetFormSectionLayout,
    HideableSimpleFieldsetFormSectionLayout,
    SimpleFieldsetFormSectionLayout, TableFormLayout)
from fred_webadmin.webwidgets.forms.formsetlayouts import DivFormSetLayout

import fred_webadmin.utils

from fred_webadmin.corba import ccReg, Registry
import fred_webadmin.corbarecoder as recoder
from fred_webadmin.webwidgets.utils import (
    ValidationError, SortedDict)

PAYMENT_UNASSIGNED = 1
PAYMENT_REGISTRAR = 2
PAYMENT_BANK = 3
PAYMENT_ACCOUNTS = 4
PAYMENT_ACADEMIA = 5
PAYMENT_OTHER = 6

# Mapping between id and user description of invoice types.
payment_map = dict([(PAYMENT_UNASSIGNED, u'Not assigned'),
(PAYMENT_REGISTRAR, u'From/to registrar'),
(PAYMENT_BANK, u"From/to bank"), 
(PAYMENT_ACCOUNTS, u'Between our own accounts'), 
(PAYMENT_ACADEMIA, u'Related to Academia'), 
(PAYMENT_OTHER, u'Other transfers')])


class UpdateFailedError(adiferrors.AdifError):
    """ To be used in fire_actions when the action cannot be carried out.
    """
    pass


class EditForm(Form):
    """ Base class for all forms used for editing objects. 
    """
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
                            '/js/MochiKit/MochiKit.js',
                            '/js/editform.js',
                            '/js/publicrequests.js']
    
    def filter_base_fields(self):
#        super(EditForm, self).filter_base_fields()
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
    def __init__(self, *args, **kwargs):
        super(ZoneEditForm, self).__init__(
            layout_class=TableFormLayout, *args, **kwargs) 

    id = HiddenIntegerField(initial=0)

    name = CharField(label=_('Name'))
    fromDate = DateField(label=_('From'))
    toDate = DateField(label=_('To'), required=False)

    def clean(self):
        """ Check that 'To' date is bigger than 'From' date. 
        """
        to_date = self.fields['toDate'].value
        from_date = self.fields['fromDate'].value
        if from_date and to_date:
            if to_date < from_date:
                raise ValidationError(
                    "'To' date must be bigger than 'From' date.")
        if 'fromDate' in self.changed_data:
            if from_date < datetime.date.today().isoformat():
                raise ValidationError("'From' date must be in future.")
        return self.cleaned_data


class SingleGroupEditForm(EditForm):
    id = ChoiceField(
        label=_('name'), 
        choices=CorbaLazyRequestIterStruct(
            'Admin', 'getGroupManager', 'getGroups', ['id', 'name'], 
            lambda groups: [g for g in groups if not g.cancelled]),
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
                old_group_id = self.initial.get('id', None)
                if old_group_id:
                    # We're chaning an already existing groups membership.
                    mgr.removeRegistrarFromGroup(reg_id, old_group_id)
                memberships = mgr.getMembershipsByRegistar(reg_id) 
                is_member = any(
                    item.group_id == group_id and not \
                    recoder.corba_to_date(item.toDate) for item in memberships)
                if not is_member:
                    # Add the registrar to a new group.
                    mgr.addRegistrarToGroup(reg_id, group_id)
            elif 'DELETE' in self.changed_data:
                mgr.removeRegistrarFromGroup(reg_id, group_id)
        except Registry.Registrar.InvalidValue, e:
            error(e)
            raise UpdateFailedError(
                "Invalid registrar group value provided")


class CertificationEditForm(EditForm):
    def __init__(self, initial=None, *args, **kwargs):
        super(CertificationEditForm, self).__init__(
            initial=initial, *args, **kwargs)
        if initial is not None:
            self['fromDate'].tattr['onfocus'] = "this.blur();"
            self['fromDate'].tattr['onclick'] = "this.blur();"
            self['fromDate'].tattr['style'] = "background:#eee none; color:#222; font-style: italic"

    id = HiddenIntegerField()
    evaluation_file_id = HiddenIntegerField()

    fromDate = DateField(label=_("From"))
    toDate = DateField(label=_("To"))
    score = IntegerChoiceField(
        choices=[(0,0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], label=_("Score")) 

    uploaded_file = CharField(
        label=_("Uploaded file"), required=False, disabled=True)
    evaluation_file = FileField(
        label=_("Upload file"), type="file", required=False)

    def clean(self):
        """ Check that 'To' date is bigger than current date
        """
        super(CertificationEditForm, self).clean()
        to_date = self.fields['toDate'].value
        from_date = date.today()
        if to_date:
            if ('toDate' in self.changed_data and 
                    to_date < from_date.strftime("%Y-%m-%d")):
                raise ValidationError(
                    "'To' date must be bigger than current date.")
        if (self.initial and self.initial.get('id', None) and
                'toDate' in self.changed_data):
            if (self.initial['toDate'].strftime("%Y-%m-%d") <
                    self.fields['toDate'].value):
                raise ValidationError(
                    "It is disallowed to lengthen the certification.")
        return self.cleaned_data

    def _get_changed_data(self):
        if self._changed_data is None:
            self._changed_data = []
            # XXX: For now we're asking the individual widgets whether or not the
            # data has changed. It would probably be more efficient to hash the
            # initial data, store it in a hidden field, and compare a hash of the
            # submitted data, but we'd need a way to easily get the string value
            # for a given field. Right now, that logic is embedded in the render
            # method of each widget.
            for name, field in self.fields.items():
                # Ignore "uploaded_file" field, because it is supposed to
                # change (it is set to the name of the uploaded file).
                if name == "uploaded_file":
                    continue
                data_value = field.value_from_datadict(self.data)
                initial_value = self.initial.get(name, field.initial)
                if field._has_changed(initial_value, data_value):
                    self._changed_data.append(name)
        return self._changed_data

    def set_fields_values(self):
        """ This is called during the form's __init__ method execution.
            Therefore, if we submit the form, this method is called when the
            form is reloaded (even if the form is not displayed and we jump
            straight to the registrar detail).
        """
        super(CertificationEditForm, self).set_fields_values()
        if not self.initial.get("id"):
            now = date.today()
            initToDate = datetime.date(
                year=now.year+1, month=now.month, day=now.day)
            # TODO(Tom): Some funny stuff is happening here, take a look at it.
            if (self.fields['toDate'].is_empty() or
                self.fields['fromDate'].is_empty()):
                # At least one of the date fields is empty => it's a new
                # certification form => fill in the defult values. If both
                # fields are filled, it's just a reload of a submitte form, 
                # so keep the data (don't change them).
                self.fields['toDate'].value = initToDate.strftime("%Y-%m-%d")
                self.fields['fromDate'].value = now.strftime("%Y-%m-%d")
            if not self.initial.get('toDate'):
                self.initial['toDate'] = initToDate
            if not self.initial.get('fromDate'):
                self.initial['fromDate'] = now
            self.initial['score'] = 0
            return
        file_id = self.initial['evaluation_file_id']
        file_mgr = cherrypy.session['FileManager']

        # Set the name of the certification evaluation file.
        info = file_mgr.info(file_id)
        self.fields['uploaded_file'].value = info.name
        self.fields['uploaded_file'].initial = info.name

    def fire_actions(self, reg_id, *args, **kwargs):
        if not self.cleaned_data or not self.changed_data:
            return
        file_mgr = cherrypy.session['FileManager']
        file_obj = self.cleaned_data['evaluation_file']
        if "evaluation_file" in self.changed_data:
            # User wants to upload a new file.
            file_upload_obj = file_mgr.save(file_obj.filename, file_obj.content.type, 6)
            chunk = file_obj.content.file.read(2**14)
            while chunk:
                file_upload_obj.upload(chunk)
                chunk = file_obj.content.file.read(2**14)
            file_id = file_upload_obj.finalize_upload()
        else:
            file_id = self.cleaned_data['evaluation_file_id']
            if not file_id:
                # This can happen when user changes something in the edit form,
                # but specifies no file to upload.
                # TODO(tom): This is wrong. Specifying file upload should be
                # mandatory. However making it mandatory breaks FormSetField 
                # validation...
                raise UpdateFailedError(
                    "You have not specified the upload file "
                    "for a certification!")
        certs_mgr = cherrypy.session['Admin'].getCertificationManager() 
        if not self.cleaned_data['id']:
            # Create a new certification.
            try:
                certs_mgr.createCertification(
                    reg_id,recoder.u2c(self.cleaned_data['fromDate']),
                    recoder.u2c(self.cleaned_data['toDate']), 
                    self.cleaned_data['score'], file_id)
            except Registry.Registrar.InvalidValue, e:
                error(e)
                raise UpdateFailedError(
                    _("Failed to create a certification. Perhaps you have "
                      "tried to create overlapping certifications?"))
        else:
            # Update an existing certifications.
            try:
                certs_mgr.updateCertification(
                    self.cleaned_data['id'], 
                    recoder.u2c(self.cleaned_data['score']), file_id)
            except Registry.Registrar.InvalidValue:
                raise UpdateFailedError(
                    "Unable to update certification.")
            if "toDate" in self.changed_data:
                cert_id = int(self.fields['id'].value)
                try:
                    certs_mgr.shortenCertification(
                        cert_id, recoder.u2c(self.cleaned_data['toDate']))
                except Registry.Registrar.InvalidValue:
                    raise UpdateFailedError(
                        "Unable to shorten certification.")


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
            'Admin', None, 'getCountryDescList', ['cc', 'name'], None), 
        initial=CorbaLazyRequest('Admin', None, 'getDefaultCountry', None), 
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

    visible_fieldsets_ids = HiddenField(
        required=False, id="visible_fieldsets_ids_field_id")
    
    access = FormSetField(
        label=_('Authentication'), form_class=AccessEditForm, can_delete=True,
        formset_layout=DivFormSetLayout)
    zones = FormSetField(
        label=_('Zones'), form_class=ZoneEditForm, 
        can_delete=False, formset_layout=DivFormSetLayout)
    groups = FormSetField(
        label=_('Groups'), form_class=SingleGroupEditForm, can_delete=True)
    certifications = FormSetField(
        label=_('Certifications'), form_class=CertificationEditForm, 
        can_delete=False)

    sections = (
        (_("Registrar data"), ("registrar_data_id"), (
            "handle", "name", "organization", 'street1', 'street2', 
            'street3', 'city', 'postalcode', 'stateorprovince', 'countryCode',
            "postalCode", "ico", "dic", "varSymb", "vat", "telephone", "fax",
            "email", "url", "id", "visible_fieldsets_ids"),
            HideableSimpleFieldsetFormSectionLayout),
        (_("Authentication"), ("authentications_id"), ("access"), 
            HideableNestedFieldsetFormSectionLayout),
        (_("Zones"), ("zones_id"), ("zones"), 
            HideableNestedFieldsetFormSectionLayout),
        (_("Groups"), ("groups_id"), ("groups"), 
            HideableNestedFieldsetFormSectionLayout),
        (_("Certifications"), ("certifications_id"), ("certifications"), 
            HideableNestedFieldsetFormSectionLayout))
    
    def filter_base_fields(self):
        """ Filters base fields against user negative permissions, so if 
            the user has nperm on the field we delete it from base_fields.
        """
        if self.nperm_names:
            user = cherrypy.session.get('user', None)
            if user is None:
                self.base_fields = SortedDict({})
            else:
                object_name = self.get_object_name()
                formset_fields = [
                    self.base_fields['access'],
                    self.base_fields['zones'],
                    self.base_fields['groups'],
                    self.base_fields['certifications']]
                for field in formset_fields:
                    if not user.check_nperms(['%s.%s.%s' % (
                            nperm_name, object_name, field.get_nperm()) for 
                            nperm_name in self.nperm_names], 'one'):
                        field.permitted = True
                    else:
                        field.permitted = False
                filtered_base_fields = SortedDict(
                    [(name, field) for name, field in self.base_fields.items()]
                )
                self.base_fields = filtered_base_fields

    def fire_actions(self, *args, **kwargs):
        try:
            reg = kwargs["updated_registrar"]
        except KeyError:
            raise RuntimeError(
                "RegistrarDataEditForm: Failed to fetch "
                "updated registrar from kwargs.")
        session = fred_webadmin.utils.get_corba_session()
        try:
            reg_id = session.updateRegistrar(reg)
        except ccReg.Admin.UpdateFailed, e:
            raise UpdateFailedError(
                "Updating registrar failed. Perhaps you tried to "
                "create a registrar with an already used handle?")
        # Set created/updated registrar id to result (it is used in ADIF
        # registrar page and other fire_action methods).
        kwargs["result"]['reg_id'] = reg_id
        # Fire actions for groups.
        self.fields["groups"].fire_actions(reg_id=reg_id, *args, **kwargs)
        self.fields["certifications"].fire_actions(
            reg_id=reg_id, *args, **kwargs)
   

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
                try:
                    log_req = cherrypy.session['Logger'].create_request(
                        cherrypy.request.headers['Remote-Addr'], 
                        cherrypy.request.body, "CreateRegistrarGroup")
                    log_req.update("group_name", group_name)
                    gid = mgr.createGroup(group_name)
                    log_req.update("group_id", gid)
                except Registry.Registrar.InvalidValue:
                    log_req.update("result", str(e))
                    raise UpdateFailedError(
                        _(u"Could not create group. Perhaps you've entered "
                           "a name of an already existing group (or name of "
                           "a deleted one, which is currently invalid too)?"))
                finally:
                    log_req.commit()
        else:
            group_id = int(group_id)
            if 'DELETE' in self.changed_data:
                try:
                    log_req = cherrypy.session['Logger'].create_request(
                        cherrypy.request.headers['Remote-Addr'], 
                        cherrypy.request.body, "DeleteRegistrarGroup")
                    log_req.update("group_name", group_name)
                    log_req.update("group_id", group_id)
                    mgr.deleteGroup(group_id)
                except Registry.Registrar.InvalidValue, e:
                    log_req.update("result", str(e))
                    log_req.update("group_id", group_id)
                    error(e)
                    raise UpdateFailedError(_(u"Group %s is not empty.") % group_name)
                finally:
                    log_req.commit()
            elif 'name' in self.changed_data:
                try:
                    log_req = cherrypy.session['Logger'].create_request(
                        cherrypy.request.headers['Remote-Addr'], 
                        cherrypy.request.body, "UpdateRegistrarGroup")
                    log_req.update("group_name", group_name)
                    log_req.update("group_id", group_id)
                    mgr.updateGroup(group_id, group_name)
                except Registry.Registrar.InvalidValue, e:
                    log_req.update("result", str(e))
                    error(e)
                    raise UpdateFailedError(_(u"Updating group %s has failed.") % group_name)
                finally:
                    log_req.commit()



class GroupManagerEditForm(EditForm):
    groups = FormSetField(
        label=_('Registrar groups'), form_class=RegistrarGroupsEditForm, 
        can_delete=True)


form_classes = [
    AccessEditForm, RegistrarEditForm, BankStatementPairingEditForm, 
    ZoneEditForm, RegistrarGroupsEditForm, SingleGroupEditForm,
    GroupManagerEditForm, CertificationEditForm]
