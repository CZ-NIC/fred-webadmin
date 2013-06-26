#!/usr/bin/python
# -*- coding: utf-8 -*-

from fred_webadmin import config
from .forms import Form
from .fields import (CharField, ChoiceField, PasswordField, HiddenField, BooleanField, MultipleChoiceFieldCheckboxes,
                     SplitDateSplitTimeField)


from fred_webadmin.translation import _
from fred_webadmin.webwidgets.forms.adiffields import ListObjectHiddenField, CorbaEnumChoiceField
from fred_webadmin.mappings import f_name_translated_plural
import cherrypy
from fred_webadmin.webwidgets.utils import ValidationError
from fred_webadmin.corba import Registry
from fred_webadmin.corbalazy import CorbaLazyRequestIterStruct

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


class DomainBlockingBase(Form): # base for all block and unblock forms
    blocking_form_sent = HiddenField(initial='1')
    objects = ListObjectHiddenField()
    blocking_action = HiddenField()
    reason = CharField(label=_('Reason'))

    def __init__(self, object_type, *content, **kwd):
        self.object_type = object_type
        super(DomainBlockingBase, self).__init__(*content, **kwd)
        self.method = 'post'
        self.fields['objects'].label = f_name_translated_plural[self.object_type].capitalize()

    def _get_submit_button_text(self):
        from fred_webadmin.controller.adif import Domain
        return Domain.blocking_types[self.fields['blocking_action'].value][1]


class DomainBlockBase(DomainBlockingBase): # base for block and change blocking form
    def build_fields(self):
        super(DomainBlockBase, self).build_fields()

        # this is here so we don't have to solve order different way (this field should be before 'blocking_status_list'
        self.fields['block_temporarily'] = BooleanField(name='block_temporarily',
                                                        label=_('Block temporarily (4 months)'))

        self.fields['blocking_status_list'] = MultipleChoiceFieldCheckboxes(
            name='blocking_status_list',
            choices=CorbaLazyRequestIterStruct('Blocking', None, 'getBlockingStatusDescList',
                                               ['shortName', 'name'], None, config.lang[:2].upper()),

            #[(item['shortName'], item['name']) for item in
             #        cherrypy.session['Blocking'].getBlockingStatusDescList(config.lang[:2].upper())],
            label=_('Blocking statuses'),
            initial=['serverDeleteProhibited', 'serverTransferProhibited', 'serverUpdateProhibited']
        )


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
        if cleaned_data['block_temporarily'] \
            and cleaned_data['owner_block_mode'] in [Registry.Administrative.BLOCK_OWNER._v,
                                               Registry.Administrative.BLOCK_OWNER_COPY._v]:
            self.add_error('owner_block_mode',
                           'You cannot use combination "Block temporarily" together with "Block the holder"'
                           ' or "Create copy of the holder" because then it\'s not possible\)'
                           ' to restore it to previous state.')
        return cleaned_data

class DomainChangeBlockingForm(DomainBlockBase):
    pass

class DomainUnblockForm(DomainBlockingBase):
    new_holder = CharField(label=_('New holder'), required=False, title=_('Leave blank to keep current holder.'))
    remove_admin_contacts = BooleanField(label=_('Remove admin. contacs'))

class DomainUnblockAndRestorePrevStateForm(DomainBlockingBase):
    new_holder = CharField(label=_('New holder'), required=False, title=_('Leave blank to restore previous holder'))

class DomainBlacklistForm(DomainBlockingBase):
    with_delete = BooleanField(label=_('Also delete the domain(s)'))
    blacklist_to_date = SplitDateSplitTimeField(label=_('To'), required=False)

class DomainUnblacklistAndCreateForm(DomainBlockingBase):
    pass
