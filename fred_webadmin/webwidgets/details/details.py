import types
import cherrypy

from dfields import DField
from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget, attr, div, a, p
from detaillayouts import SectionDetailLayout
from fred_webadmin.webwidgets.utils import SortedDict
from fred_webadmin.translation import _


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
    nperm_names = ['read']

    def __init__(self, data, history, label_suffix=':', display_only=None,
                 sections=None, layout_class=SectionDetailLayout,
                 is_nested=False, all_no_access=False, *content, **kwd):
        super(BaseDetail, self).__init__(*content, **kwd)
        self.tag = u''
        self.media_files.append('/css/details.css')

        self.history = history
        self.data = data or {}
        if data is not None:
            if not isinstance(data, types.DictType):  # data is some corba object
                self.data = data.__dict__
            else:  # data is dict
                self.data = data

        self.label_suffix = label_suffix
        self.layout_class = layout_class
        self.is_nested = is_nested
        self.all_no_access = all_no_access

        # check if display_only contains correct field names
        if display_only:
            for field_name in display_only:
                if self.base_fields.get(field_name) is None:
                    raise RuntimeError(_('Incorrect field name "%s" specified in %s. display_only list!') % (field_name, repr(self)))

        self.display_only = display_only

        # Sections can be defined as class attribute of detail, so take care
        # to create attribute but not override it, if it already exists.
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
        """ Filters base fields against user negative permissions,
            so if user has nperm on field we delete it from base_fields.
        """
        user = cherrypy.session.get('user', None)
        if user is None:
            self.base_fields = SortedDict({})
        else:
            self.base_fields = SortedDict(
                [(name, field) for name, field in self.base_fields.items()
                    if not self.display_only or field.name in self.display_only])

    def build_fields(self):
        user = cherrypy.session.get('user', None)
        if user is None:
            self.fields = SortedDict({})
        else:
            self.fields = self.base_fields.deepcopy()
            object_name = self.get_object_name()
            for field in self.fields.values():
                field_nperm = field.get_nperm()
                if self.all_no_access or user.check_nperms(
                    ['%s.%s.%s' % (nperm_name, object_name, field_nperm) for \
                        nperm_name in self.nperm_names], 'one'):
                            field.access = False
                field.owner_detail = self

    def set_fields_values(self):
        for field in self.fields.values():
            field.value = field.value_from_data(self.data)

    @classmethod
    def get_object_name(cls):
        return cls.__name__[:-len('Detail')].lower()

    def add_to_bottom(self):
        ''' Usualy used for filterpanel and/or edit link. '''
        if self.editable:
            self.add(p(a(attr(href=u'../edit/?id=' + unicode(self.data.get('id'))), _('Edit'))))

    def render(self, indent_level=0):
        self.content = []  # empty previous content (if render would be called moretimes, there would be multiple forms instead one )
        self.add(self.layout_class(self))
        if self.check_nperms():
            # TODO: render error!
            return div("ERROR NO PERMS").render()
            pass
        if not self.is_nested:
            self.add_to_bottom()
        return super(BaseDetail, self).render(indent_level)

    def check_nperms(self):
        return False

    @classmethod
    def get_nperms(cls):
        nperms = []
        for field in cls.base_fields.values():
            field_nperm = field.get_nperm()
            field_nperms = ['%s.%s.%s' % (nperm_name, cls.get_object_name(), field_nperm) for nperm_name in cls.nperm_names]
            nperms.extend(field_nperms)
        return nperms


class Detail(BaseDetail):
    __metaclass__ = DeclarativeDFieldsMetaclass
