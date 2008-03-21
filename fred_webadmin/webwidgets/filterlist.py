#!/usr/bin/python
# -*- coding: utf-8 -*-

from gpyweb.gpyweb import WebWidget, attr, save, ul, li, a
from fred_webadmin.mappings import f_urls, f_id_name
from fred_webadmin.translation import _

class FilterList(ul):
    def __init__(self, filters, filter_name=None, *content, **kwd):
        ''' Filters is list of triplets [id, type, name] 
            If filter_name is specified, general filter for that object is added (e.g. /domains/filter/)
        '''
        super(FilterList, self).__init__(*content, **kwd)
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
            
            