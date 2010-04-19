#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import simplejson
from logging import debug
import cherrypy

from gpyweb.gpyweb import WebWidget, attr, save, ul, li, a, table, tr, th, td, b, form, textarea, input, script
from fred_webadmin.mappings import f_urls, f_id_name, f_name_filterformname
from fred_webadmin.translation import _
from fred_webadmin.itertable import IterTable
from fred_webadmin.webwidgets.forms.filterforms import UnionFilterForm
from fred_webadmin.webwidgets.forms.filterforms import *

class FilterList(ul):
    def __init__(self, filters, filter_name=None, *content, **kwd):
        ''' Filters is list of triplets [id, type, name] 
            If filter_name is specified, general filter for that object is added (e.g. /domains/filter/)
        '''
        super(FilterList, self).__init__(*content, **kwd)
        self.tag = 'ul'
        debug('LIST OF FILTERS: %s' % filters)
        for filter in filters:
            url_filter = f_urls[f_id_name[int(filter['Type'])]] + 'filter/?filter_id=' + filter['Id']
            url_filter_with_form =  url_filter + '&show_form=1'
            self.add(li(
                        a(attr(href=url_filter), filter['Name']),
                        ' (', a(attr(href=url_filter_with_form), _('form')),  ')',
                       ))
        if filter_name:
            self.add(li(a(attr(href=f_urls[filter_name] + 'filter/'), _('Custom filter'))))
    def _get_form_class(self, filter_name):
        form_name = f_name_filterformname[filter_name]
        form_class = getattr(sys.modules[self.__module__], form_name, None)
        if not form_class:
            raise RuntimeError('No such formclass in modules "%s"' % form_name)
        return form_class
    def get_form(self, filter):
        key = cherrypy.session.get('corbaSessionString', '')
        itertable = IterTable(f_id_name[int(filter['Type'])], key)
        itertable.load_filter(int(filter['Id']))
        if not itertable.all_fields_filled():
            filter_data = itertable.get_filter_data()
            form_class = self._get_form_class(f_id_name[int(filter['Type'])])
            form = UnionFilterForm(filter_data, data_cleaned=True, form_class=form_class)
        else:
            form = ''
        return form
                
class FilterListUnpacked(FilterList):
    def __init__(self, filters, filter_name=None, *content, **kwd):
        ''' Filters is list of triplets [id, type, name] 
            If filter_name is specified, general filter for that object is added (e.g. /domains/filter/)
        '''
        ul.__init__(self, *content, **kwd)
        self.tag = 'ul'
        debug('LIST OF FILTERS(unpacked): %s' % filters)
        for filter in filters:
            url_filter = f_urls[f_id_name[int(filter['Type'])]] + 'filter/?filter_id=' + filter['Id']
            url_filter_with_form =  url_filter + '&show_form=1'
            form = self.get_form(filter)
            self.add(li(
                        a(attr(href=url_filter), filter['Name']),
                        ' (', a(attr(href=url_filter_with_form), _('form')),  ')',
                        form))
        if filter_name:
            self.add(li(a(attr(href=f_urls[filter_name] + 'filter/'), _('Custom filter'))))
            
        self.add(script(attr(type='text/javascript'), 'Ext.onReady(function () {addFieldsButtons()})')) 

class FilterListCustomUnpacked(FilterList):
    
    def __init__(self, filters, filter_name=None, *content, **kwd):
        ''' Filters is list of triplets [id, type, name] 
            If filter_name is specified, general filter for that object is added (e.g. /domains/filter/)
        '''
        ul.__init__(self, *content, **kwd)
        self.tag = 'ul'
        debug('LIST OF FILTERS(unpacked): %s' % filters)
        
        custom_presented = False
        for filter in filters:
            url_filter = f_urls[f_id_name[int(filter['Type'])]] + 'filter/?filter_id=' + filter['Id']
            url_filter_with_form =  url_filter + '&show_form=1'
            if filter['Name'].lower() == 'custom':
                form = self.get_form(filter)
                custom_presented = True
            else:
                form = None
            self.add(li(
                        a(attr(href=url_filter), filter['Name']),
                        ' (', a(attr(href=url_filter_with_form), _('form')),  ')',
                        form))
        if not custom_presented and filter_name:
            self.add(li(a(attr(href=f_urls[filter_name] + 'filter/'), _('Custom filter')),
                        self.get_default_form(filter_name)
                       ))
            
        self.add(script(attr(type='text/javascript'), 'Ext.onReady(function () {addFieldsButtons()})')) 

    def get_default_form(self, filter_name):
        return UnionFilterForm(form_class=self._get_form_class(filter_name))
        
    
class FilterPanel(table):
    ''' Used in detail view of objects. It is panel with buttons to filters related to 
        currently displayed object (like admins of domain in domain detail view).
        Button can also be just simple link.
    '''
    def __init__(self, filters, *content, **kwd):
        ''' filters is list of tripplet [button_label, object_name, filters] where filters in linear form. written
            (e.g. [{'domain.registrar.handle'='ahoj', 'handle'=[True, 'ahoj']}] (True is for negation))
            (so if there is negation, then value is list [value, negation], otherwise it is just value)
            Alternatively, instead of filter (which is a triplet), can be used direct link (couple):
            [button_label, url]
        '''
        super(FilterPanel, self).__init__(*content, **kwd)
        self.tag = 'table'
        
        filter_count = len(filters)
        self.add(attr(cssc='filter_panel'),
                 tr(th(attr(colspan=filter_count), b(_('Options')))),
                 tr(save(self, 'filter_buttons')))

        for button_data in filters:
            if len(button_data) == 2:
                button_label, url = button_data
                self.filter_buttons.add(
                    td(a(attr(href = url), _(button_label))))
            elif len(button_data) == 3:
                button_label, obj_name, filter = button_data
                self.filter_buttons.add(
                    td(form(
                        attr(
                            action=f_urls[obj_name] + 'filter/', 
                            method='POST'),
                        textarea(
                            attr(
                                style='display: none', 
                                name='json_linear_filter'),
                            simplejson.dumps(filter)),
                        input(attr(type='submit', value=_(button_label))))))
            
        
    
    
    
