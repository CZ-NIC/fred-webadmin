#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime

from fred_webadmin import config
from .forms import Form
from .fields import (CharField, ChoiceField, PasswordField, HiddenField, BooleanField, MultipleChoiceFieldCheckboxes,
                     DateField)
from .adiffields import DateFieldWithJsLink

from fred_webadmin.translation import _
from fred_webadmin.webwidgets.forms.adiffields import ListObjectHiddenField, CorbaEnumChoiceField
from fred_webadmin.mappings import f_name_translated_plural
from fred_webadmin.corba import Registry
from fred_webadmin.corbalazy import CorbaLazyRequestIterStruct
from fred_webadmin.webwidgets.utils import ValidationError

#__all__ = ['LoginForm', 'FilterForm']


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
                                               ['shortName', 'name'], None, config.lang[:2].upper()),
            label=_('Blocking statuses'),
            initial=['serverDeleteProhibited', 'serverTransferProhibited', 'serverUpdateProhibited']
        )

    def clean_block_to_date(self):
        if self.cleaned_data['block_to_date'] and self.cleaned_data['block_to_date'] <= datetime.date.today():
            raise ValidationError('Block to date must be in the future.')


class DomainBlockForm(DomainBlockBase):
    owner_block_mode = CorbaEnumChoiceField(
        label=_('Holder blocking'), corba_enum=Registry.Administrative.OwnerBlockMode,
        enum_translation_mapping={
            'KEEP_OWNER': _('Do not block the holder'),
            'BLOCK_OWNER': _('Block the holder'),
            'BLOCK_OWNER_COPY': _('Create copy of the holder'),
        }
    )

    def clean(self):
        cleaned_data = super(DomainBlockForm, self).clean()
        print "BLOCK MODE", cleaned_data['owner_block_mode']
        if cleaned_data.get('block_to_date') \
            and cleaned_data['owner_block_mode'] == Registry.Administrative.BLOCK_OWNER_COPY:
            self.add_error('owner_block_mode',
                           'You cannot use combination "Block to date" together with "Create copy of the holder"'
                           'because then it\'s not possible to automatically restore the previous holder.')
        return cleaned_data


class DomainChangeBlockingForm(DomainBlockBase):
    pass


class DomainUnblockForm(DomainBlockingBase):
    new_holder = CharField(label=_('New holder'), required=False, title=_('Leave blank to keep current holder.'))
    remove_admin_contacts = BooleanField(label=_('Remove admin. contacs'))


class DomainUnblockAndRestorePrevStateForm(DomainBlockingBase):
    new_holder = CharField(label=_('New holder'), required=False, title=_('Leave blank to restore previous holder'))


class DomainBlacklistAndDeleteForm(DomainBlockingBase):
    blacklist_to_date = DateFieldWithJsLink(label=_('To'),
                                            link_add_months_count=config.blacklisting_link_add_month_count,
                                            required=False)

    def clean_blacklist_to_date(self):
        if self.cleaned_data['blacklist_to_date'] and self.cleaned_data['blacklist_to_date'] <= datetime.date.today():
            raise ValidationError('Blacklist to date must be in the future.')


class DomainUnblacklistAndCreateForm(DomainBlockingBase):
    pass
