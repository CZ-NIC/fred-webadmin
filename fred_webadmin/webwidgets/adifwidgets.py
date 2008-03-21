#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson

from gpyweb.gpyweb import WebWidget, attr, save, ul, li, a, table, tr, th, td, b, form, textarea, input
from fred_webadmin.mappings import f_urls, f_id_name
from fred_webadmin.translation import _

class FilterList(ul):
    def __init__(self, filters, filter_name=None, *content, **kwd):
        ''' Filters is list of triplets [id, type, name] 
            If filter_name is specified, general filter for that object is added (e.g. /domains/filter/)
        '''
        super(FilterList, self).__init__(*content, **kwd)
        self.tag = 'ul'
        print 'VYLISTOVANE FILTERY:', filters
        for filter in filters:
            url_filter = f_urls[f_id_name[int(filter['Type'])]] + 'filter/?filter_id=' + filter['Id']
            url_filter_with_form =  url_filter + '&show_form=1'
            self.add(li(
                        a(attr(href=url_filter), filter['Name']),
                        ' (', a(attr(href=url_filter_with_form), _('form')),  ')',
                       ))
        if filter_name:
            self.add(li(a(attr(href=f_urls[filter_name] + 'filter/'), _('Custom filter'))))
            

class FilterPanel(table):
    ''' Used in detail view of objects. It ispanel with buttons to filters related to 
        currently displayed object (lie admins of domain in domain detail view)
    '''
    def __init__(self, filters, *content, **kwd):
        ''' filters is list of tripplet [button_label, object_name, filters] whre filters in linear form. written
            (e.g. [{domain.registrar.handle='ahoj', handle=['ahoj', True]}] (True is for negation))
        '''
        super(FilterPanel, self).__init__(*content, **kwd)
        self.tag = 'table'
        
        
        filter_count = len(filters)
        self.add(attr(style='width: 96%', border='1'),
                 tr(th(attr(colspan=filter_count), b(_('Options')))),
                 tr(save(self, 'filter_buttons')))
        for button_label, obj_name, filter in filters.items():
            self.filter_buttons.add(
                td(form(attr(action = f_urls[obj_name] + 'filter', method='POST'), 
                        textarea(attr(style='display: none', name='filter_nssetHandle'),
                                 simplejson.dumps(filter)), 
                        input(attr(type='submit', value=_(button_label))))) 
            )
        
    
    
    