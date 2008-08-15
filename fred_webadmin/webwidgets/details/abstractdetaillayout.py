import types

from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget
from fred_webadmin.webwidgets.utils import pretty_name

class AbstractDetailLayout(WebWidget):
    ''' Common parent class for DetailLayouts and SectionLayouts (look at SectionDetailLayout)'''
    def __init__(self, detail, *content, **kwd):
        super(AbstractDetailLayout, self).__init__(*content, **kwd)
        self.detail = detail
        
        
    def get_label_name(self, field_or_string):
        if isinstance(field_or_string, types.StringTypes): 
            label_str = field_or_string
        else:
            label_str = field_or_string.label
        
        if label_str == '': # if empty string is explicitly specified, it really should return empty string
            return ''
        
        if not label_str:
            label_str = pretty_name(field_or_string.name)
        if self.detail.label_suffix and label_str[-1] not in ':?.!':
            label_str += self.detail.label_suffix
        return label_str