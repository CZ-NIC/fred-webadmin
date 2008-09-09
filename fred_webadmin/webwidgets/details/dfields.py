#!/usr/bin/python
# -*- coding: utf-8 -*-

from copy import copy
import cherrypy
from omniORB.any import from_any
from omniORB import CORBA

from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget, tagid, attr, noesc, a, img, strong, div, span, pre, table, thead, tbody, tr, th, td
from fred_webadmin.mappings import f_urls
from detaillayouts import SectionDetailLayout, TableRowDetailLayout, TableColumnsDetailLayout
from fred_webadmin.utils import get_detail_from_oid
from fred_webadmin.translation import _
from fred_webadmin.utils import corba_to_datetime, LateBindingProperty
from fred_webadmin.corba import ccReg, Registry
from fred_webadmin.webwidgets.xml_prettyprint import xml_prettify_webwidget
from fred_webadmin.mappings import f_enum_name, f_name_detailname
import fred_webadmin.webwidgets.details.adifdetails# as details_module

def resolve_object(obj_data):
    ''' Returns object from data, where data could be OID, OID in CORBA.Any, or just data isself
    '''
    if isinstance(obj_data, CORBA.Any):
        obj_data = from_any(obj_data, True)

    if isinstance(obj_data, Registry.OID):
        if obj_data.id != 0:
            return get_detail_from_oid(obj_data)
        else:
            return None
    else:
        return obj_data
    
#def resolve_detail_class(obj_data):
#    ''' Detect detail class if object is OID or OID in CORBA.Any'''
#    if isinstance(obj_data, CORBA.Any):
#        obj_data = from_any(obj_data, True)
#    if isinstance(obj_data, Registry.OID):
#        detail_name = f_name_detailname[f_enum_name[obj_data.type]]
#        detail_class = getattr(fred_webadmin.webwidgets.details.adifdetails, detail_name, None)
#        return detail_class
        

class DField(WebWidget):
    ''' Base class for detail fields '''
    creation_counter = 0
    
    def __init__(self, name='', label=None, *content, **kwd):
        super(DField, self).__init__(*content, **kwd)
        self.tag = ''
        self.name = name
        self.label = label
        self.owner_form = None
        self._value = None
        self.access = True # if user have nperm for this field, than detail.filter
        self.no_access_content = span(attr(style='background-color: gray;'), _('CENSORED'))
        
        # Increase the creation counter, and save our local copy.
        self.creation_counter = DField.creation_counter
        DField.creation_counter += 1
    
    def on_add(self):
        if not self.access and self.parent_widget:
            self.parent_widget.style = 'background-color: gray;'
        
    def make_content(self):
        self.content = []
        if self.value == '':
            self.add(div(attr(cssc='field_empty')))
        else:
            self.add(self._value)
        
    def make_content_no_access(self):
        self.content = []
        self.add(self.no_access_content)
    
    def resolve_value(self, value):
        return value    
    
    def _set_value(self, value):
        self._value = self.resolve_value(value)
        self.make_content()
    def _get_value(self):
        return self._value
    value = LateBindingProperty(_get_value, _set_value)
    
    def value_from_data(self, data):
        return data.get(self.name)
    
    def render(self, indent_level=0):
        if not self.access:
            self.make_content_no_access()
        return super(DField, self).render(indent_level)
    
class CharDField(DField):
    enclose_content = True
    def resolve_value(self, value):
        if value is not None:
            value = unicode(value)
        return value
    
class PreCharDField(CharDField):
    ''' Content text is in <pre> html tag. '''
    def make_content(self):
        self.content = []
        if self.value == '':
            self.add(div(attr(cssc='field_empty')))
        else:
            self.add(pre(self._value))

class XMLDField(CharDField):
    enclose_content = True
    def __init__(self, name='', label=None, *content, **kwd):
        super(XMLDField, self).__init__(*content, **kwd)
        self.media_files.append('/css/pygments.css')
    def resolve_value(self, value):
        value = super(XMLDField, self).resolve_value(value)
        value = xml_prettify_webwidget(value)
        return value
        
class EmailDField(CharDField):
    def make_content(self):
        self.content = []
        if self._value == '':
            self.add(div(attr(cssc='field_empty')))
        if self._value:
            self.add(a(attr(href='mailto:' + self._value), self._value))
            
class ListCharDField(CharDField):
    def resolve_value(self, value):
        return ', '.join([unicode(sub_val) for sub_val in value])
            

class CorbaEnumDField(CharDField):
    def resolve_value(self, value):
        if value is not None:
            value = _(value._n)
        value = super(CorbaEnumDField, self).resolve_value(value)
        return value
        
    
    
class ObjectHandleDField(DField):
    def make_content(self):
        self.content = []
        oid = self._value
        if oid is not None:
            self.add(a(attr(href=f_urls[f_enum_name[oid.type]] + u'detail/?id=' + unicode(oid.id)), 
#                       strong(oid.handle)))
                       oid.handle))            
        else:
            self.add(div(attr(cssc='field_empty')))

class MultiValueDField(DField):
    ''' Field that takes some values from data of form and store them to self.value as dict. 
        Method that takes value from data of form can be overriden,
        so it can be used to create data from 2 HistoryRecordList fields etc.
    '''
    def __init__(self, name='', label=None, field_names=None, *content, **kwd):
        super(MultiValueDField, self).__init__(name, label, *content, **kwd)
        if field_names is None:
            raise RuntimeError('Field names of multivalue field must be specified!')
        self.field_names = field_names

    def value_from_data(self, data):
        val = {}
        for field_name in self.field_names:
            val[field_name] = data.get(field_name)
        return self.resolve_value(val)
            

class ObjectHandleURLDField(MultiValueDField):
    ''' Field that is not from OID. It creates link from id and handle paramaters. 
        object_type_name (e.g. 'domain') is eigther given as parametr to constructor or just read from fields owner_detail name, 
        It reads data from fields given in constructor (usualy "id" and "handle").
    '''
    enclose_content = True
    def __init__(self, name='', label=None, id_name = 'id', handle_name = 'handle', object_type_name=None, *content, **kwd):
        super(ObjectHandleURLDField, self).__init__(name, label, [id_name, handle_name], *content, **kwd)
        self.id_name = id_name
        self.handle_name = handle_name
        self.object_type_name = object_type_name
            
            
    def make_content(self):
        self.content = []

        if self.object_type_name is None: # this cannot be in constructor, becouse self.owner_detail is not known at construction time
            self.object_type_name = self.owner_detail.get_object_name() 

        if self.value[self.handle_name] == '':
            self.add(div(attr(cssc='field_empty')))
        self.add(a(attr(href=f_urls[self.object_type_name] + 'detail/?id=%s' % self.value[self.id_name]), self.value[self.handle_name]))
        
#    def value_from_data(self, data):
#        return self.resolve_value([data.get(self.id_name), data.get(self.handle_name)])

class DiscloseCharDField(CharDField):
    ''' Field which get additional boolean value (usualy dislose + self.name.capitalize(), but can be specified),
        and display main value in span with red or greed background according to dislose value flag).
    '''
    def __init__(self, name='', label=None, disclose_name = None, *content, **kwd):
        super(DiscloseCharDField, self).__init__(name, label, *content, **kwd)
        if disclose_name is None:
            self.disclose_name = 'disclose' + self.name.capitalize()
        else:
            self.disclose_name = disclose_name
        
    def make_content(self):
        self.content = []
        cssc = 'disclose' + self.value[1] # => 'discloseTrue' or 'discloseFalse'
        self.add(span(attr(cssc=cssc), self.value[0]))
        
    def value_from_data(self, data):
        return self.resolve_value([data.get(self.name), data.get(self.disclose_name)])
    
    

class ObjectHandleEPPIdDField(DField):
    def __init__(self, name='', label=None, handle_name = 'handle', eppid_name = 'roid', *content, **kwd):
        super(ObjectHandleEPPIdDField, self).__init__(name, label, *content, **kwd)
        self.handle_name = handle_name
        self.eppid_name = eppid_name
    
    def make_content(self):
        self.content = []
        if self.value == ['', '']:
            self.add(div(attr(cssc='field_empty')))
        self.add(strong(self.value[0]), span(attr(cssc='epp'), '(EPP id:', self.value[1], ')'))
        
    def value_from_data(self, data):
        return self.resolve_value([data.get(self.handle_name), data.get(self.eppid_name)])

class PriceDField(DField):
    def make_content(self):
        self.content = []
        if self.value == ['', '', '', '']:
            self.add(div(attr(cssc='field_empty')))
        self.add(strong(self.value[0]), span(_(u'(%s + %s of %s%% VAT)') % tuple(self.value[1:])))
        
    def value_from_data(self, data):
        return self.resolve_value([data.get('price'), data.get('total'), data.get('totalVAT'), data.get('vatRate')])
    
    
class ObjectDField(DField):
    '''Field with inner object detail'''
    def __init__(self, name='', label=None, detail_class = None, display_only = None, sections=None, layout_class=SectionDetailLayout, *content, **kwd):
        super(ObjectDField, self).__init__(name, label, *content, **kwd)
        self.detail_class = detail_class
        
        self.display_only = display_only
        self.sections = sections
        self.layout_class = layout_class
    
    def resolve_value(self, value):
        if self.detail_class is None:
            self.detail_class = resolve_detail_class(value)
        return resolve_object(value)
    
    def create_inner_detail(self):
        '''Used by make_content and in custom detail layouts and custom section layouts'''
        self.inner_detail = self.detail_class(self.value, self.owner_detail.history, display_only=self.display_only, sections=self.sections, layout_class=self.layout_class, is_nested=True)
        
    def make_content(self):
        from fred_webadmin.webwidgets.details.adifdetails import NSSetDetail 
        self.content = []
        self.create_inner_detail()
        self.add(self.inner_detail)

class ListObjectDField(DField):
    ''' Field with inner list of objects - displayed in table where headers are labels, 
    '''
    tattr_list = table.tattr_list
    def __init__(self, detail_class = None, display_only = None, layout_class=TableRowDetailLayout, *content, **kwd): 
        super(ListObjectDField, self).__init__(*content, **kwd)
        self.tag = u'table'
        self.detail_class = detail_class
        self.display_only = display_only
        self.layout_class = layout_class
        
        self.cssc = u'section_table history_list_table' # although this is not a section table, it is mostly used in DirectSectionLayout, so it is in place where SectionTable is and so it should have the same style
        
        
    def resolve_value(self, value):
        # tady asi bude neco jak if isinstance(data, OID_type), tak tohle, else: a ziskani dat specifikovane nepovinnym parametrem (jmeno funkce nebo ukazaetel na funkci)
        # navic je tu jeste treti moznost, ze objekt je nejaka struktura, tudis je to primo corba structura - v takovem pripade se musi vzit jen data.__dict__
        if value:
            new_value = []
            for obj_data in value:
                new_value.append(resolve_object(obj_data))
            return new_value
        return value
    
    
    def create_inner_details(self):
        '''Used by make_content and in custom detail layouts and custom section layouts'''
        self.inner_details = []
        if self.value:
            for value in self.value:
                self.inner_details.append(self.detail_class(value, self.owner_detail.history, display_only=self.display_only, layout_class=self.layout_class, is_nested=True))
     
    def make_content(self):
        self.content = []
        self.create_inner_details()
        
        if self.inner_details:
            # Header:
            thead_row = tr()
            for field in self.inner_details[0].fields.values():
                thead_row.add(th(field.label))
            self.add(thead(thead_row))
            
            # rows (each row is made from one detail of object in object list
            self.add(tbody(tagid('tbody')))
            for detail in self.inner_details:
                self.tbody.add(detail)
#                print "pridavam dtail detail"
#                for field in detail.fields:
#                    print 'adding field field.name'
#                    row.add(td(field))
#                self.add(row)
        else:
            self.add(div(attr(cssc='field_empty')))

class ListObjectHandleDField(DField):
    ''' Data is list of OIDs.
    '''
    enclose_content = True
    def make_content(self):
        self.content = []
        if self.value:
            for i, oid in enumerate(self.value):
                if oid and oid.id:
                    if i != 0:
                        self.add(',')
                    self.add(a(attr(href=f_urls[f_enum_name[oid.type]] + u'detail/?id=' + unicode(oid.id)), 
    #                           strong(oid.handle)))
                               oid.handle))
                
class ConvertDField(DField):
    ''' Converts source value to another value, rendering it to other field. 
        Parametr 'convert_table' is dict or list or tupple of couples (source_value, convert_to_value)
    ''' 
    def __init__(self, name='', label=None, inner_field = None, convert_table = None, *content, **kwd):
        super(ConvertDField, self).__init__(name, label, *content, **kwd)
        if convert_table is None:
            raise RuntimeError('You must specify convert_table in ConvertDField')
        self.convert_table = convert_table
        self.inner_field = copy(inner_field)
        
    def make_content(self):
        self.inner_field.value = self.convert_table[self.value]
        self.add(self.inner_field)

class HistoryDField(DField):   
    ''' Only for history part of NHDfield, so this field is not used directly in detail
    '''
    tattr_list = table.tattr_list
    def __init__(self, name='', label=None, inner_field = None, *content, **kwd):
        super(HistoryDField, self).__init__(name, label, *content, **kwd)
        self.tag = 'table'
        self.cssc = 'history_list_table'
        
        self.inner_field = copy(inner_field)
        
    def make_content(self):
        self.content = []

        self.inner_field.owner_detail = self.owner_detail
        if self.value:
            for i, history_rec in enumerate(self.value):
                val = from_any(history_rec.value, True)
                inner_field_copy = copy(self.inner_field)
                inner_field_copy.value = val
                date_from = corba_to_datetime(history_rec._from)
                date_to = corba_to_datetime(history_rec.to)
                action_url = f_urls['action'] + 'detail/?id=%s' % history_rec.actionId
                
                history_tr = tr()
                if i > 0:
                    history_tr.cssc = 'history_row'
                history_tr.add(
                    td(inner_field_copy),
                    td(attr(cssc='history_dates_field'), _('from'), date_from),
                    td(attr(cssc='history_dates_field'), date_to and _('to') or '', date_to),
                    td(attr(cssc='history_dates_field'), a(href=action_url), img(attr(src='/img/icons/open.png')))
                )
                
                self.add(history_tr)
        else:
            self.add(div(attr(cssc='field_empty')))


    
    def on_add(self):
        if self.parent_widget and self.parent_widget.tag == 'td':
            self.parent_widget.style = 'padding: 0px'

class HistoryObjectDField(HistoryDField):
    ''' History field of inner object - displayed in table where headers are labels, 
    '''
    tattr_list = table.tattr_list
    def __init__(self, detail_class = None, display_only = None, layout_class=TableColumnsDetailLayout, *content, **kwd): 
        super(HistoryObjectDField, self).__init__(*content, **kwd)
        self.tag = u'table'
        self.detail_class = detail_class
        self.display_only = display_only
        self.layout_class = layout_class
        
        self.cssc = u'section_table history_list_table' # although this is not a section table, it is mostly used in DirectSectionLayout, so it is in place where SectionTable is and so it should have the same style
    
    def resolve_value(self, value):
        if value:
            for history_row in value:
                history_row.value = resolve_object(history_row.value)
        return value
    
    def create_inner_details(self):
        '''Used by make_content and in custom detail layouts and custom section layouts'''
        self.inner_details = []
        if self.value:
            for history_row in self.value:
                self.inner_details.append(self.detail_class(history_row.value, self.owner_detail.history, display_only=self.display_only, layout_class=self.layout_class, is_nested=True))
     
    def make_content(self):
        self.content = []
        self.create_inner_details()
        
        if self.inner_details:
            # Header:
            thead_row = tr()
            for field in self.inner_details[0].fields.values():
                thead_row.add(th(field.label))
            thead_row.add(th(_('From')), th(_('To')), th(_('A.')))
            self.add(thead(thead_row))
            
            # rows (each row is made from one detail of object in object list
            self.add(tbody(tagid('tbody')))
            for i, detail in enumerate(self.inner_details):
                history_rec = self.value[i]
                date_from = corba_to_datetime(history_rec._from)
                date_to = corba_to_datetime(history_rec.to)
                action_url = f_urls['action'] + 'detail/?id=%s' % history_rec.actionId
                
                history_tr = tr()
                if i > 0:
                    history_tr.cssc = 'history_row'
                history_tr.add(
                    detail,
                    td(attr(cssc='history_dates_field'), date_from),
                    td(attr(cssc='history_dates_field'), date_to),
                    td(attr(cssc='history_dates_field'), a(href=action_url), img(attr(src='/img/icons/open.png')))
                )
                self.add(history_tr)
        else:
            self.add(div(attr(cssc='field_empty')))            
    
class HistoryListObjectDField(HistoryDField):            
    tattr_list = table.tattr_list
    def __init__(self, detail_class = None, display_only = None, layout_class=TableColumnsDetailLayout, *content, **kwd): 
        super(HistoryListObjectDField, self).__init__(*content, **kwd)
        self.tag = u'table'
        self.detail_class = detail_class
        self.display_only = display_only
        self.layout_class = layout_class
        
        self.cssc = u'section_table history_list_table' # although this is not a section table, it is mostly used in DirectSectionLayout, so it is in place where SectionTable is and so it should have the same style
        
    def resolve_value(self, value):
        if value:
            for history_row in value:
                if isinstance(history_row.value, CORBA.Any):
                    object_list = from_any(history_row.value, True)
                else: # this HistoryRecordList was transformed before (we got here after cache hit), so skip tranformation
                    break
                new_obj_list = []
                for obj in object_list:
                    new_obj_list.append(resolve_object(obj))
                history_row.value = new_obj_list
        return value
    
    def create_inner_details(self):
        '''Used by make_content and in custom detail layouts and custom section layouts'''
        self.inner_details = [] # list of lists of deatils (one level for history, second for objects in list)
        
        if self.value:
            for history_row in self.value:
                inner_detail_list = []
                
                for obj_data in history_row.value:
                    inner_detail_list.append(self.detail_class(obj_data, self.owner_detail.history, display_only=self.display_only, layout_class=self.layout_class, is_nested=True))
                self.inner_details.append(inner_detail_list)
     
    def make_content(self):
        self.content = []
        self.create_inner_details()
                    
        if self.inner_details and self.inner_details[0]:
            # Header:
            thead_row = tr()
            for field in self.inner_details[0][0].fields.values():
                thead_row.add(th(field.label))
            thead_row.add(th(_('From')), th(_('To')), th(_('A.')))
            self.add(thead(thead_row))
            
            # rows (each row is made from one detail of object in object list
            self.add(tbody(tagid('tbody')))
            for i, detail in enumerate(self.inner_details):
                history_rec = self.value[i]
                date_from = corba_to_datetime(history_rec._from)
                date_to = corba_to_datetime(history_rec.to)
                action_url = f_urls['action'] + 'detail/?id=%s' % history_rec.actionId
                
                for j, detail in enumerate(self.inner_details[i]):
                    row = tr()
                    row.cssc = ''
                    if i > 0:
                        row.cssc += ' history_row'
                    row.add(
                        detail,
                    )
                    if j == 0:
                        row.cssc += ' history_division_row'
                        rowspan_attr = attr(rowspan=len(self.inner_details[i]), cssc='history_dates_field')
                        row.add(
                            td(rowspan_attr, date_from),
                            td(rowspan_attr, date_to),
                            td(rowspan_attr, a(href=action_url), img(attr(src='/img/icons/open.png')))
                        )
                    self.add(row)
        else:
            self.add(div(attr(cssc='field_empty')))    
         

class NHDField(DField):
    ''' Normal and History field combined in one. Depending of history flag of detail,
        one of them is used for render
    '''
    def __init__(self, normal_field, history_field, *content, **kwd):
        self.normal_field = normal_field
        self.history_field = history_field
        self.delegate_methods = [
            'on_add', 'make_content', 'make_content_no_access', 'resolve_value', 'value_from_data', 'render'
        ]
        self._owner_detail = None
        self.displaying_history = False
        super(NHDField, self).__init__(*content, **kwd)
    
#    def get_current_field(self):
#        if self.owner_detail.history and len(self._value) > 1:
#            return self.history_field
#        else:
#            return self.normal_field
    
    def value_from_data(self, data):
        value = data.get(self.name)
        
        if value is not None:
            if self.owner_detail.history and len(value) > 1 and not self.owner_detail.is_nested:
                self.displaying_history = True
                self.history_field.owner_detail = self.owner_detail
                self.current_field = self.history_field
                return value
            else:
                self.normal_field.owner_detail = self.owner_detail
                self.current_field = self.normal_field
                return from_any(value[0].value, True)
        else:
            self.normal_field.owner_detail = self.owner_detail
            self.current_field = self.normal_field
            
        
    def _set_value(self, value):
        self._value = self.current_field.value = self.resolve_value(value)
        self.current_field.make_content()
    def _get_value(self):
        return self.current_field._value
    
    def _set_owner_detail(self, value):
        self._owner_detail = self.normal_field.owner_detail = self.history_field.owner_detail = value
    def _get_owner_detail(self):
        return self._owner_detail
    owner_detail = LateBindingProperty(_get_owner_detail, _set_owner_detail)
    
    def on_add(self):
        self.current_field.parent_widget = self.parent_widget
        self.current_field.on_add() 
        

    def render(self, indent_level=0):
        return self.current_field.render(indent_level)
    
    
class CharNHDField(NHDField):
    def __init__(self, *content, **kwd):
        super(CharNHDField, self).__init__(CharDField(), HistoryDField(inner_field = CharDField()), *content, **kwd)

class DiscloseCharNHDField(NHDField):
    def __init__(self, *content, **kwd):
        super(DiscloseCharNHDField, self).__init__(DiscloseCharDField(), HistoryDField(inner_field=DiscloseCharDField()), *content, **kwd)
    
    def value_from_data(self, data):
        value_name = data.get(self.name)
        value_disclose = data.get(self.disclose_name)
        
        
        
        
        if self.owner_detail.history and len(value) > 1 and not self.owner_detail.is_nested:
            self.displaying_history = True
            self.history_field.owner_detail = self.owner_detail
            self.current_field = self.history_field
            return value
        elif value:
            self.normal_field.owner_detail = self.owner_detail
            self.current_field = self.normal_field
            return from_any(value[0].value, True)
    
    