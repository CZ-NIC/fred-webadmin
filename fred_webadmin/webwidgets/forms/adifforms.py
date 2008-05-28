#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

sys.path.insert(0, '')

from logging import debug

from fred_webadmin import config
from forms import Form
from fields import *
from adiffields import *

from fred_webadmin.translation import _

#__all__ = ['LoginForm', 'FilterForm']

class LoginForm(Form):
    corba_server = ChoiceField(choices=[(str(i), ior[0]) for i, ior in enumerate(config.iors)], label=_("Server"))
    login = CharField(max_length=30, label=_('Username'))#, initial=_(u'ohíňěček ťůříšekňú'))
    password = PasswordField(max_length=30)
    next = HiddenField(initial='/')
    media_files = 'form_files.js'

