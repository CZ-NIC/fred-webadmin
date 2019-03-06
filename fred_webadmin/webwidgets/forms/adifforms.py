#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2018  CZ.NIC, z. s. p. o.
#
# This file is part of FRED.
#
# FRED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FRED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FRED.  If not, see <https://www.gnu.org/licenses/>.

from logging import error
import csv
import datetime


from fred_webadmin import config
from .forms import Form
from .fields import (BooleanField, CharField, ChoiceField, FileField, HiddenField, MultipleChoiceFieldCheckboxes,
                     PasswordField)
from .adiffields import DateFieldWithJsLink

from fred_webadmin.translation import _
from fred_webadmin.webwidgets.forms.adiffields import ListObjectHiddenField, CorbaEnumChoiceField
from fred_webadmin.webwidgets.forms.fields import SplitDateSplitTimeField
from fred_webadmin.mappings import f_name_translated_plural
from fred_webadmin.corba import Registry
from fred_webadmin.corbalazy import CorbaLazyRequestIterStruct
from fred_webadmin.webwidgets.utils import ValidationError


class LoginForm(Form):
    corba_server = ChoiceField(choices=[(str(i), ior[0]) for i, ior in enumerate(config.iors)], label=_("Server"))
    login = CharField(max_length=30, label=_('Username'), autofocus='autofocus')
    password = PasswordField(max_length=30)
    next = HiddenField(initial='/')
    media_files = 'form_files.js'
    submit_button_text = _('Login')


class OpenIDLoginForm(Form):
    corba_server = ChoiceField(choices=[(str(i), ior[0]) for i, ior in enumerate(config.iors)], label=_("Server"))
    login = CharField(max_length=30, label=_('Username'))
    # Hide password (OpenID prompts for password at a different place).
    password = HiddenField(max_length=30)
    next = HiddenField(initial='/')
    media_files = 'form_files.js'


class DomainBlockingBase(Form):
    objects = ListObjectHiddenField()
    blocking_action = HiddenField()
    reason = CharField(label=_('Reason'))
    object_type = 'domain'

    def __init__(self, *content, **kwd):
        super(DomainBlockingBase, self).__init__(*content, **kwd)
        self.method = 'post'
        self.fields['objects'].label = f_name_translated_plural[self.object_type].capitalize()
        self.media_files.append('/js/submit_confirmation.js')
        self.add_css_class('confirm_submit')

    def _get_submit_button_text(self):
        from fred_webadmin.controller.adif import Domain
        return Domain.blocking_views[self.fields['blocking_action'].value].action_name


class DomainBlockBase(DomainBlockingBase):  # base for block and change blocking form
    def build_fields(self):
        super(DomainBlockBase, self).build_fields()

        # this is here so we don't have to solve order different way (this field should be before 'blocking_status_list'
        self.fields['block_to_date'] = DateFieldWithJsLink(name='block_to_date',
                                                           link_add_months_count=config.blocking_link_add_month_count,
                                                           label=_('Block to date'), required=False)
        self.fields['blocking_status_list'] = MultipleChoiceFieldCheckboxes(
            name='blocking_status_list',
            choices=CorbaLazyRequestIterStruct('Blocking', None, 'getBlockingStatusDescList',
                                               ['shortName', 'name'], None, None, config.lang[:2].upper()),
            label=_('Blocking statuses'),
            initial=['serverDeleteProhibited', 'serverTransferProhibited', 'serverUpdateProhibited']
        )

    def clean_block_to_date(self):
        if self.cleaned_data['block_to_date'] and self.cleaned_data['block_to_date'] <= datetime.date.today():
            raise ValidationError('Block to date must be in the future.')
        return self.cleaned_data['block_to_date']


class DomainBlockForm(DomainBlockBase):
    owner_block_mode = CorbaEnumChoiceField(
        label=_('Holder blocking'), corba_enum=Registry.Administrative.OwnerBlockMode,
        enum_translation_mapping={
            'KEEP_OWNER': _('Do not block the holder'),
            'BLOCK_OWNER': _('Block the holder'),
            'BLOCK_OWNER_COPY': _('Create copy of the holder'),
        }
    )


class DomainChangeBlockingForm(DomainBlockBase):
    pass


class DomainUnblockForm(DomainBlockingBase):
    new_holder = CharField(label=_('New holder'), required=False)
    remove_admin_contacts = BooleanField(label=_('Remove admin. contacts'))
    restore_prev_state = BooleanField(label=_('Restore prev. state'),
                                      title=_('Restores previous user blocking and the previous holder,'
                                              ' if the field "New holder" is empty.'))

    def clean(self):
        cleaned_data = super(DomainUnblockForm, self).clean()
        if cleaned_data.get('restore_prev_state') and cleaned_data.get('remove_admin_contacts'):
            self.add_error('remove_admin_contacts', _('You cannot use "Remove admin. contacts" and "Restore prev. state"'
                                                     ' at the same time.'))

        if not cleaned_data.get('restore_prev_state') and not cleaned_data.get('new_holder'):
            self.add_error('new_holder', _('New holder is required when you don\'t use "Restore prev. state"'))

        return cleaned_data


class DomainBlacklistAndDeleteForm(DomainBlockingBase):
    blacklist_to_date = DateFieldWithJsLink(label=_('To'),
                                            link_add_months_count=config.blacklisting_link_add_month_count,
                                            required=False)

    def clean_blacklist_to_date(self):
        if self.cleaned_data['blacklist_to_date'] and self.cleaned_data['blacklist_to_date'] <= datetime.date.today():
            raise ValidationError('Blacklist to date must be in the future.')
        return self.cleaned_data['blacklist_to_date']


class DomainUnblacklistAndCreateForm(DomainBlockingBase):
    pass


class ImportNotifEmailsForm(Form):
    EMAILS_COLUMN = 'Email list'
    ID_COLUMN = 'Id'

    domains_emails = FileField(label=_("Upload file"), type="file", required=True)

    submit_button_text = _('Save')

    def __init__(self, *content, **kwd):
        super(ImportNotifEmailsForm, self).__init__(*content, **kwd)
        self.method = 'post'
        self.enctype = 'multipart/form-data'

    def clean_domains_emails(self):
        csv_file = self.cleaned_data['domains_emails'].content.file
        try:
            reader = csv.DictReader(csv_file)
            if not reader.fieldnames:
                raise ValidationError('Wrong file format.')
            if self.EMAILS_COLUMN not in reader.fieldnames:
                raise ValidationError('Missing column "%s" in the file.' % self.EMAILS_COLUMN)
            if self.ID_COLUMN not in reader.fieldnames:
                raise ValidationError('Missing column "%s" in the file.' % self.ID_COLUMN)

            domain_email_list = []
            for row_num, row in enumerate(reader, start=2):  # data in spreadsheet starts on line 2
                if row[self.ID_COLUMN] is None:
                    raise ValidationError('Missing column "%s" on the row %d.' % (self.ID_COLUMN, row_num))
                if row[self.EMAILS_COLUMN] is None:
                    raise ValidationError('Missing column "%s" on the row %d.' % (self.EMAILS_COLUMN, row_num))
                try:
                    domain_id = int(row[self.ID_COLUMN])
                except ValueError:
                    raise ValidationError('Invalid value in column Id: "%s". It must be a whole number.' %
                                          row[self.ID_COLUMN])
                emails = row[self.EMAILS_COLUMN].strip()
                if emails.strip():
                    email_list = emails.split(',')
                    for email in email_list:
                        domain_email_list.append((domain_id, email.strip()))
            return domain_email_list
        except csv.Error, e:
            error('Error during reading CSV:', e)
            raise ValidationError('A correct CSV file is needed!')


class ObjectPrintoutForm(Form):
    for_time = SplitDateSplitTimeField(label=_('For the date'), required=True)

    submit_button_text = _('Download PDF')

    def __init__(self, *content, **kwd):
        super(ObjectPrintoutForm, self).__init__(*content, **kwd)
        self.method = 'post'
        self.fields['for_time'].fields[0].required = True

    def clean_for_time(self):
        if self.cleaned_data['for_time'] and self.cleaned_data['for_time'] > datetime.datetime.now():
            raise ValidationError('Record statement date must not be in the future.')
        return self.cleaned_data['for_time']
