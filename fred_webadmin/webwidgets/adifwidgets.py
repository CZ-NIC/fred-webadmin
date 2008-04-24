#!/usr/bin/python
# -*- coding: utf-8 -*-

import simplejson
from logging import debug

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
            

class FilterPanel(table):
    ''' Used in detail view of objects. It ispanel with buttons to filters related to 
        currently displayed object (lie admins of domain in domain detail view)
    '''
    def __init__(self, filters, *content, **kwd):
        ''' filters is list of tripplet [button_label, object_name, filters] where filters in linear form. written
            (e.g. [{domain.registrar.handle='ahoj', handle=[True, 'ahoj']}] (True is for negation))
            (so if there is negation, then value is list [value, negaion], otherwise it is just value)
            Alternatively, instead of filter (which is triplet), can be used direct link (couple):
            [button_label, url]
        '''
        super(FilterPanel, self).__init__(*content, **kwd)
        self.tag = 'table'
        
        
        filter_count = len(filters)
        self.add(attr(style='width: 96%', border='1'),
                 tr(th(attr(colspan=filter_count), b(_('Options')))),
                 tr(save(self, 'filter_buttons')))
        for button_data in filters:
            if len(button_data) == 2:
                button_label, url = button_data
                
                self.filter_buttons.add(
                    td(form(attr(action = url, method='POST'), 
                            input(attr(type='submit', value=_(button_label))))) 
                )

            elif len(button_data) == 3:
                button_label, obj_name, filter = button_data

                self.filter_buttons.add(
                    td(form(attr(action = f_urls[obj_name] + 'filter/', method='POST'), 
                            textarea(attr(style='display: none', name='json_linear_filter'),
                                     simplejson.dumps(filter)), 
                            input(attr(type='submit', value=_(button_label))))) 
                )
            
        
    
    
    