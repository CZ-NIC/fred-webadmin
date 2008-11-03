import types
import cherrypy
from logging import debug

from dfields import DField
from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget, attr, div, a, p
from detaillayouts import TableDetailLayout, SectionDetailLayout
from fred_webadmin.webwidgets.utils import SortedDict
from fred_webadmin.utils import get_detail_from_oid
from fred_webadmin.corba import ccReg
from fred_webadmin.translation import _
from fred_webadmin.corba import Registry

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

        attrs['base_fields'] = SortedDict(fields)
        for i, (field_name, field) in enumerate(attrs['base_fields'].items()):
            field.name = field_name
            field.order = i
            

        new_class = type.__new__(cls, name, bases, attrs)
        return new_class
    
    
class BaseDetail(div):
    editable = False
    
    def __init__(self, data, history, label_suffix=':', display_only = None, sections = None, layout_class=SectionDetailLayout,#TableDetailLayout,
                 is_nested = False, *content, **kwd):
        super(BaseDetail, self).__init__(*content, **kwd)
        self.tag = u''
        self.media_files.append('/css/details.css')

        self.history = history
        self.data = data or {}
        if data is not None:
            if isinstance(data, ccReg.PublicRequest.OID): # data is OID (object id)
                self.data = get_detail_from_oid(data).__dict__
            elif not isinstance(data, types.DictType): # data is some corba object
                self.data = data.__dict__
            else: # data is dict
                self.data = data
            
        self.label_suffix = label_suffix
        self.layout_class = layout_class
        self.is_nested = is_nested
        
        # check if display_only contains correct field names
        if display_only:
            for field_name in display_only:
                if self.base_fields.get(field_name) is None:
                    raise RuntimeError(_('Incorrect field name "%s" specified in %s. display_only list!') % (field_name, repr(self)))
             
        self.display_only = display_only
        
        # sections can be devined as class attribute of detail, so take care to create attribute but not override it, if it already exists
        if getattr(self, 'sections', None) is None: 
            self.sections = None
        if sections is not None:
            self.sections = sections
        
        self.fields = None
        self.filter_base_fields()
        self.build_fields()
        self.set_fields_values()

        # if self.section is None, create one default section with all fields:
        if self.sections is None or sections == 'all_in_one':
            self.sections = [[None, self.fields.keys()]]

    def filter_base_fields(self):
        "Filters base fields against user negative permissions, so if user has nperm on field we delete it from base_fields"
        user = cherrypy.session.get('user', None)
        #import pdb; pdb.set_trace()
        if user is None:
            self.base_fields = SortedDict({})
#                self.default_fields_names = []
        else:
            object_name = self.get_object_name()
            #self.base_fields = SortedDict([(name, field) for name, field in self.base_fields.items()])
            #nself.base_fields = SortedDict(self.base_fields)
#            self.base_fields = SortedDict([(name, field) for name, field in self.base_fields.items() 
#                                           if not user.has_nperm('%s.%s.%s' % (object_name, 'detail', field.name)) and (not self.display_only or field.name in self.display_only)
#                                          ])
            
            for name, field in self.base_fields.items():
                if user.has_nperm('%s.%s.%s' % (object_name, 'detail', field.name)):
                    field.access = False
            
            self.base_fields = SortedDict([(name, field) for name, field in self.base_fields.items() 
                                           if not self.display_only or field.name in self.display_only
                                          ])
#                self.default_fields_names = [field_name for field_name in self.default_fields_names if field_name in self.base_fields.keys()]
    
    def build_fields(self):
        self.fields = self.base_fields.deepcopy()
        for field in self.fields.values():
            field.owner_detail = self
        
    def set_fields_values(self):
        for field in self.fields.values():
            if field.access:
                field.value = field.value_from_data(self.data)
#            else:
#                print 'No access field "%s", not setting value' % field.name 
    
    @classmethod
    def get_object_name(cls):
        return cls.__name__[:-len('Detail')].lower()
    
    def add_to_bottom(self):
        ''' Usualy used for filterpanel and/or edit link. '''
        if self.editable:
            self.add(p(a(attr(href=u'../edit/?id=' + unicode(self.data.get('id'))), _('Edit'))))
    
    def render(self, indent_level=0):
        self.content = [] # empty previous content (if render would be called moretimes, there would be multiple forms instead one )
        debug('Adding layout %s to %s' % (self.layout_class, self.__class__.__name__))
        self.add(self.layout_class(self))
        if not self.is_nested:
            self.add_to_bottom()
        debug('After adding layout %s to %s' % (self.layout_class, self.__class__.__name__))
        return super(BaseDetail, self).render(indent_level)        
            
class Detail(BaseDetail):
    __metaclass__ = DeclarativeDFieldsMetaclass
