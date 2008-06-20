#!/usr/bin/python
# -*- coding: utf-8 -*-

import cherrypy

from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget, attr, a, strong
from fred_webadmin.mappings import f_urls, f_objectType_name
from detaillayouts import SectionDetailLayout
from fred_webadmin.utils import get_detail_from_oid

class DField(WebWidget):
    ''' Base class for detail fields '''
    creation_counter = 0
    
    def __init__(self, name='', label=None, *content, **kwd):
        super(DField, self).__init__(*content, **kwd)
        self.tag = ''
        self.label = label
        self.owner_form = None
        self._value = None
        
        # Increase the creation counter, and save our local copy.
        self.creation_counter = DField.creation_counter
        DField.creation_counter += 1
        
    def make_content(self):
        self.content = []
        self.add(self._value)
        
    def _set_value(self, value):
        self._value = value
        self.make_content()
    def _get_value(self):
        return self._value
    value = property(_get_value, _set_value)
    
    def value_from_data(self, data):
        return data.get(self.name)
    
class CharDField(DField):
    def value_from_data(self, data):
        value = data.get(self.name)
        if value is not None:
            value = unicode(value)
        return value
    
class EmailDField(CharDField):
    def make_content(self):
        self.content = []
        if self._value:
            self.add(a(attr(href='mailto:' + self._value), self._value))
                     
    
class ObjectHadleDField(DField):
    def make_content(self):
        self.content = []
        oid = self._value
        if oid is not None:
            self.add(a(attr(href=f_urls[f_objectType_name[oid.type]] + 'detail/?id=' + unicode(oid.id)), 
                       strong(oid.handle)))
        

class ObjectField(DField):
    '''Field with inner object detail'''
    def __init__(self, name='', label=None, detail_class = None, display_only = None, sections=None, layout_class=SectionDetailLayout, *content, **kwd):
        super(ObjectField, self).__init__(name, label, *content, **kwd)
        self.detail_class = detail_class
        self.display_only = display_only
        self.sections = sections
        self.layout_class = layout_class
    
    def value_from_data(self, data):
        value = get_detail_from_oid(data.get(self.name))
        return value
    
    def make_content(self):
        self.content = []
        detail = self.detail_class(self.value, display_only=self.display_only, sections=self.sections, layout_class = self.layout_class)
        self.add(detail)

class ListObjectField(DField):
    pass


