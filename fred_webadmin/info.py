#!/usr/bin/python
# -*- coding: utf-8 -*-

from itertools import chain

from fred_webadmin.webwidgets.forms.filterforms import form_classes as filter_form_classes 
from fred_webadmin.webwidgets.forms.editforms import form_classes as edit_form_classes
from fred_webadmin.webwidgets.details.adifdetails import detail_classes

def print_nperms(distinct=False):
    nperms = []
    for form_class in chain(filter_form_classes, edit_form_classes, detail_classes):
        nperms.extend(form_class.get_nperms())
    print '\nList of all nperms of following forms and details:'
    print ', '.join([cls.__name__ for cls in chain(filter_form_classes, edit_form_classes, detail_classes)]) + '\n'
    if distinct:
        nperms = list(set(nperms))
    print '\n'.join(sorted(nperms))
    print '\n(%d nperms total)' % len(nperms)

def print_nperms_for_class(class_name):
    form_class = None
    for form_class in chain(filter_form_classes, edit_form_classes, detail_classes):
        if form_class.__name__ == class_name:
            break
    if form_class and form_class.__name__ == class_name:
        print 'Nperms for %s:' % class_name
        print '\n'.join(form_class.get_nperms())
    else:
        print '\nNo such class: %s' % class_name
    