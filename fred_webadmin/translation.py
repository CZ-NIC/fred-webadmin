#!/usr/bin/python
# -*- coding: utf-8 -*-

import gettext
import config


####################################
# gettext
####################################

translate = gettext.translation(config.gettext_domain, config.localepath, languages=[config.lang]).ugettext

_ = translate

#def _(key, encoding='utf-8'):
#   return translate(key).decode(encoding)
#   #return translate(key)#.decode(encoding)

####################################
