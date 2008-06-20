import types
import cherrypy
from logging import debug

from dfields import DField
from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget, div
from detaillayouts import TableDetailLayout, SectionDetailLayout
from fred_webadmin.webwidgets.forms.forms import SortedDictFromList
from fred_webadmin.webwidgets.utils import SortedDict
from fred_webadmin.utils import get_detail_from_oid
from fred_webadmin.corba import ccReg

class DeclarativeDFieldsMetaclass(WebWidget.__metaclass__):
    """
    Metaclass that converts DField attributes to a dictionary called
    'base_fields', taking into account parent class 'base_fields' as well.
    """
    def __new__(cls, name, bases, attrs):
        fields = [(field_name, attrs.pop(field_name)) for field_name, obj in attrs.items() if isinstance(obj, DField)]
        fields.sort(lambda x, y: cmp(x[1].creation_counter, y[1].creation_counter))

        # If this class is subclassing another Detail, add that Detail's fields.
        # Note that we loop over the bases in *reverse*. This is necessary in
        # order to preserve the correct order of fields.
        debug('%s|%s|%s|%s' % (cls, name, bases, attrs))

        for base in bases[::-1]:
            if hasattr(base, 'base_fields'):
                fields = base.base_fields.items() + fields

        attrs['base_fields'] = SortedDictFromList(fields)
        for i, (field_name, field) in enumerate(attrs['base_fields'].items()):
            field.name_orig = field.name = field_name
            field.order = i

        new_class = type.__new__(cls, name, bases, attrs)
        return new_class
    
    
class BaseDetail(div):
    def __init__(self, data=None, label_suffix=':', display_only = None, sections = None, layout_class=SectionDetailLayout,#TableDetailLayout,
                 is_nested = False, *content, **kwd):
        super(BaseDetail, self).__init__(*content, **kwd)
        
        self.tag = u'div'
        self.data = data or {}
        if isinstance(data, ccReg.PublicRequest.OID): # data is OID (object id)
            self.data = get_detail_from_oid(data).__dict__
        elif not isinstance(data, types.DictType): # data is some corba object
            self.data = data.__dict__
        else: # data is dict
            self.data = data
            
            

        self.label_suffix = label_suffix
        self.layout_class = layout_class
        self.is_nested = is_nested
        self.display_only = display_only
        if sections is not None:
            self.sections = sections 

        self.fields = None
        self.filter_base_fields()
        self.build_fields()
        self.set_fields_values()


    def filter_base_fields(self):
        "Filters base fields against user negative permissions, so if user has nperm on field we delete it from base_fields"
        user = cherrypy.session.get('user', None)
        #import pdb; pdb.set_trace()
        if user is None:
            self.base_fields = SortedDict({})
#                self.default_fields_names = []
        else:
            object_name = self.get_object_name()
            self.base_fields = SortedDict([(name, field) for name, field in self.base_fields.items() 
                                           if not user.has_nperm('%s.%s.%s' % (object_name, 'detail', field.name)) and (not self.display_only or field.name in self.display_only)
                                          ])
#                self.default_fields_names = [field_name for field_name in self.default_fields_names if field_name in self.base_fields.keys()]

    @classmethod
    def get_object_name(cls):
        return cls.__name__[:-len('Detail')].lower()
    
    def build_fields(self):
        self.fields = self.base_fields.copy()
        for field in self.fields.values():
            field.owner_detail = self
        
    def set_fields_values(self):
        for field in self.fields.values():
            field.value = field.value_from_data(self.data)
    
    
    
    def render(self, indent_level=0):
        self.content = [] # empty previous content (if render would be called moretimes, there would be multiple forms instead one )
        debug('Adding layout %s to %s' % (self.layout_class, self.__class__.__name__))
        self.add(self.layout_class(self))
        debug('After adding layout %s to %s' % (self.layout_class, self.__class__.__name__))
        return super(BaseDetail, self).render(indent_level)        
            
class Detail(BaseDetail):
    __metaclass__ = DeclarativeDFieldsMetaclass