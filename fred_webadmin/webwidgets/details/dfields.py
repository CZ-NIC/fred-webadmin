#!/usr/bin/python
# -*- coding: utf-8 -*-

from copy import copy
import cherrypy
from omniORB.any import from_any, to_any
from omniORB import CORBA
from datetime import datetime
import time

import fred_webadmin.corbarecoder as recoder
import fred_webadmin.nulltype as fredtypes

from fred_webadmin import config
from fred_webadmin.webwidgets.gpyweb.gpyweb import WebWidget, tagid, attr, noesc, a, img, strong, div, span, pre, table, thead, tbody, tr, th, td
from fred_webadmin.mappings import f_urls
from detaillayouts import SectionDetailLayout, TableRowDetailLayout, TableColumnsDetailLayout
from fred_webadmin.utils import get_detail_from_oid, LateBindingProperty
from fred_webadmin.translation import _
from fred_webadmin.corba import ccReg, Registry
from fred_webadmin.webwidgets.xml_prettyprint import xml_prettify_webwidget
from fred_webadmin.mappings import f_enum_name, f_name_detailname
from fred_webadmin.corbalazy import CorbaLazyRequestIter

def resolve_object(obj_data):
    """ Returns object from data, where data could be OID, OID in CORBA.Any, 
        or just data itself
    """
    if isinstance(obj_data, CORBA.Any):
        obj_data = from_any(obj_data, True)

    if isinstance(obj_data, Registry.OID):
        if obj_data.id != 0:
            return get_detail_from_oid(obj_data)
        else:
            return None
    else:
        if obj_data is None:
            return fredtypes.Null()
        else:
            return obj_data
    
class DField(WebWidget):
    ''' Base class for detail fields '''
    creation_counter = 0
    
    def __init__(self, name='', label=None, nperm = None, *content, **kwd):
        super(DField, self).__init__(*content, **kwd)
        self.tag = ''
        self.name = name
        self.label = label
        self._nperm = nperm
        self.owner_form = None
        self._value = fredtypes.Null() #None
        self.access = True # if user have nperm for this field, then this will be set to False in Detail.build_fields()
        self.no_access_content = div(attr(cssc='no_access'), _('CENSORED'))
        
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
        if value is None:
            return fredtypes.Null()
        else:
            return value    
    
    def _set_value(self, value):
        if self.access:
            self._value = self.resolve_value(value)
            self.make_content()
        else:
            self._value = fredtypes.Null() #None
            self.make_content_no_access()
    def _get_value(self):
        return self._value
    value = LateBindingProperty(_get_value, _set_value)
    
    def value_from_data(self, data):
        if data.get(self.name) is None:
            return fredtypes.Null()
        else:
            return data.get(self.name)
    
    def render(self, indent_level=0):
        return super(DField, self).render(indent_level)

    def get_nperm(self):
        if self._nperm:
            return self._nperm.lower()
        else:
            return self.name.lower()
           
class CharDField(DField):
    enclose_content = True
    def resolve_value(self, value):
        if value != fredtypes.Null():
            value = unicode(value)
        return value

#TODO(tom): Really convert here? Or is it already converted when
# converting corba detail?
class DateDField(DField):
    enclose_content = True
    def resolve_value(self, value):
        if value != fredtypes.Null():
            value = recoder.corba_to_date(value)
        return fredtypes.NullDate()


class LongCharDField(DField):
    enclose_content = True
    n_break_chars = 40 # number of chars after that char_break is inserted
    break_char = '<br />'
    def resolve_value(self, value):
        val = super(LongCharDField, self).resolve_value(value)
        splitted = [val[self.n_break_chars*i:self.n_break_chars*(i+1)] for i in range(len(val)/self.n_break_chars + 1)]
        return noesc(self.break_char.join(splitted))
        
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
        if self._value == '' or isinstance(self._value, fredtypes.Null):
            self.add(div(attr(cssc='field_empty')))
        if self._value:
            self.add(a(attr(href='mailto:' + self._value), self._value))


class ListCharDField(CharDField):
    def resolve_value(self, value):
        return ', '.join([unicode(sub_val) for sub_val in value])
            

class CorbaEnumDField(CharDField):
    def resolve_value(self, value):
        if value != fredtypes.Null():
            value = _(value._n)
        value = super(CorbaEnumDField, self).resolve_value(value)
        return value


class RequestPropertyDField(DField):
    """ ccReg.RequestProperty detail field. 
        Note: Currently only used by LoggerDetail.
    """
    def __init__(self, name='', label=None, *content, **kwd):
        DField.__init__(self, name, label, *content, **kwd)


    def _separate_properties(self, props):
        """
            >>> props = [\
                    ccReg.RequestProperty(name='foo', value='0', \
                        output=True, child=False), \
                    ccReg.RequestProperty(\
                        name='bar', value='4', \
                        output=False, child=False)]
            >>> inp, out = RequestPropertyDField()._separate_properties(props)
            >>> len(inp) == 1
            True
            >>> len(out) == 1
            True
        """
        inp, out = [], []
        for prop in props:
            if prop.output:
                inp.append(prop)
            else:
                out.append(prop)
        return (inp, out)
        
    def resolve_value(self, value):
        """ Handles displayed value formatting.

            Args:
                value: List of ccReg.RequestProperty objects.
        """
        inprops, outprops = self._separate_properties(value)
        return div(
            table([self._format_property(prop) for prop in inprops]),
            table([self._format_property(prop) for prop in outprops]))

    def _format_property(self, prop):
        return tr(td("%s:" % prop.name), td("%s" % prop.value))

    
class ObjectHandleDField(DField):
    def make_content(self):
        self.content = []
        oid = self._value
        if oid is not None:
            self.add(a(attr(href=f_urls[f_enum_name[oid.type]] + u'detail/?id=' + unicode(oid.id)), 
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

class DiscloseCharDField(DField):
    ''' Field which get additional boolean value (usualy dislose + self.name[1].upper() + self.name[1:], but can be specified),
        and display main value in span with red or greed background according to dislose value flag).
    '''
    def make_content(self):
        self.content = []
        if self.value:
            cssc = 'disclose' + unicode(bool(self.value[1])) # => 'discloseTrue' or 'discloseFalse'
            if self.value[0] == '':
                self.add(div(attr(cssc=cssc + ' field_empty')))
            else:
                self.add(span(attr(cssc=cssc), self.value[0]))
        else:
            self.add(div(attr(cssc='field_empty'))) # in case no access (from permissions)
    
    def on_add(self):
        super(DiscloseCharDField, self).on_add()
        if self.parent_widget and self.value:
            cssc = 'disclose' + unicode(bool(self.value[1])) # => 'discloseTrue' or 'discloseFalse'
            if getattr(self.parent_widget, 'cssc', False):
                self.parent_widget.cssc += ' ' + cssc
            else:
                self.parent_widget.cssc = cssc

#    def value_from_data(self, data):
#        return self.resolve_value([data.get(self.name), data.get(self.disclose_name)])
    
    

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
        return resolve_object(value)
    
    def create_inner_detail(self):
        '''Used by make_content and in custom detail layouts and custom section layouts'''
        self.inner_detail = self.detail_class(self.value, self.owner_detail.history, display_only=self.display_only, sections=self.sections, layout_class=self.layout_class, is_nested=True, all_no_access=not self.access)
        
    def make_content(self):
#        from fred_webadmin.webwidgets.details.adifdetails import NSSetDetail 
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

        # Although this is not a section table, it is mostly used in 
        # DirectSectionLayout, so it is in the same place as SectionTable.
        # Ergo it should have the same style.
        self.cssc = u'section_table history_list_table' 
        
        
    def resolve_value(self, value):
        # tady asi bude neco jak if isinstance(data, OID_type), tak tohle, else: a ziskani dat specifikovane nepovinnym parametrem (jmeno funkce nebo ukazaetel na funkci)
        # navic je tu jeste treti moznost, ze objekt je nejaka struktura, tudis je to primo corba structura - v takovem pripade se musi vzit jen data.__dict__
        if value:
            new_value = []
            for obj_data in value:
                new_value.append(resolve_object(obj_data))
            return new_value
        return value
    
    
    def _create_inner_details(self):
        '''Used by make_content and in custom detail layouts and custom section layouts'''
        self.inner_details = []
        if self.value:
            for value in self.value:
                self.inner_details.append(
                    self.detail_class(
                        value, 
                        self.owner_detail.history, 
                        display_only=self.display_only, 
                        layout_class=self.layout_class, 
                        is_nested=True))
     
    def make_content(self):
        self.content = []
        self._create_inner_details()
        
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
        Parametr 'convert_table' is dict or list or tuple of couples (source_value, convert_to_value)
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
                date_from = recoder.corba_to_datetime(history_rec._from)
                date_to = recoder.corba_to_datetime(history_rec.to)
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
        super(HistoryDField, self).on_add()
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
        if value is None:
            return fredtypes.Null()
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
                date_from = recoder.corba_to_datetime(history_rec._from)
                date_to = recoder.corba_to_datetime(history_rec.to)
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
        if value is None():
            return fredtypes.Null()
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
        def _add_row(i, j, detail):
            row = tr()
            row.cssc = ''
            if i > 0:
                row.cssc += ' history_row'
            if detail:
                row.add(detail)
            else:
                row.add(td(attr(colspan=len(thead_row.content) - 3), div(attr(cssc='field_empty'))))
            if j == 0:
                row.cssc += ' history_division_row'
                rowspan_attr = attr(rowspan=len(self.inner_details[i]) or 1, cssc='history_dates_field')
                row.add(
                    td(rowspan_attr, date_from),
                    td(rowspan_attr, date_to),
                    td(rowspan_attr, a(href=action_url), img(attr(src='/img/icons/open.png')))
                )
            self.add(row)
            
            
        self.content = []
        self.create_inner_details()

        if self.inner_details:
            # Header:
            thead_row = tr()
            #  Find one (any of them) innter detail for obtaining field labels (cannot take first one, becouse firt can be empty list):
            some_detail = None
            for details in self.inner_details:
                if details:
                    some_detail = details[0]
                    break
                
            for field in some_detail.fields.values():
                thead_row.add(th(field.label))
            thead_row.add(th(_('From')), th(_('To')), th(_('A.')))
            self.add(thead(thead_row))
            
            # rows (each row is made from one detail of object in object list
            self.add(tbody(tagid('tbody')))
            for i in range(len(self.inner_details)):
                history_rec = self.value[i]
                date_from = recoder.corba_to_datetime(history_rec._from)
                date_to = recoder.corba_to_datetime(history_rec.to)
                action_url = f_urls['action'] + 'detail/?id=%s' % history_rec.actionId
                
                if self.inner_details[i]:
                    for j, detail in enumerate(self.inner_details[i]):
                        _add_row(i, j, detail)
                else:
                    _add_row(i, 0, None)
                    
        else:
            self.add(div(attr(cssc='field_empty')))    

class HistoryStateDField(DField):
    ''' Field that display actual states or history of states.'''
    def __init__(self, name='', label=None, *content, **kwd):
        super(HistoryStateDField, self).__init__(name, label, *content, **kwd)
        self.corba_states_desc = CorbaLazyRequestIter('Admin', 'getObjectStatusDescList', config.lang[:2])
        self.state_list = []
        self.states_desc = {}
        self.states_name = {}
        self.states_abbrev = {}
        self.media_files.append('/js/boxover.js')

    def resolve_value(self, value):
        if not self.state_list:
            for corba_state_desc in self.corba_states_desc:
                self.state_list.append(corba_state_desc.id)
                self.states_desc[corba_state_desc.id] = corba_state_desc.name 
                self.states_name[corba_state_desc.id] = corba_state_desc.shortName
                self.states_abbrev[corba_state_desc.id] = self.get_state_abbrev_from_name(corba_state_desc.shortName) #tady budou dvoupismenne zkratky, budto generovane, nebo z mapping.py
            
        new_states = []
        if value:
            for state in value:
                new_state = {}
                new_state['id'] = state.id
                new_state['from'] = recoder.corba_to_datetime(state._from)
                if state.to is None:
                    import pdb; pdb.set_trace()
                new_state['to'] = recoder.corba_to_datetime(state.to)
                new_state['linked'] = state.linked
                new_states.append(new_state)
        return new_states
    
    def compute_state_data(self):
        all_dates = {}

        # all dates dict (from AND to), keys are dates, values are lists of [ couples 'from' or 'to' strings and state dicts (references to states in self.value)] 
        for state in self.value:
            if state['from']:
                if all_dates.get(state['from']) is None:
                    all_dates[state['from']] = [['from', state]]
                else:
                    all_dates[state['from']].append(['from', state])
            if state['to']:
                if all_dates.get(state['to']) is None:
                    all_dates[state['to']] = [['to', state]]
                else:
                    all_dates[state['to']].append(['to', state])
            
        # row is dict containing all states_id as key and value is boolean (state is off, state is on)
        current_row = dict([(state_id, False) for state_id in self.state_list])
        current_row['row_date'] = None
        
        # state_table is list of rows, each row is copy of current_row for given date
        state_table = []
        
        for date, from_to_state_list in sorted(all_dates.items()):
            current_row['row_date'] = date
            for from_to_state in from_to_state_list:
                from_to = from_to_state[0]
                state = from_to_state[1]
                
                if from_to == 'from':
                    current_row[state['id']] = True
                elif from_to == 'to':
                    current_row[state['id']] = False
                else:
                    raise RuntimeError('Variable from_to must be "from" or "to"!')
            new_row = dict(current_row) # copy of current row
            state_table.append(new_row)
        
        state_table = list(reversed(state_table))
        
        return state_table
    
    def get_state_abbrev_from_name(self, name):
        ''' Get state abbrev from state name. It ignores 'server' and 'validation' on beggining of name.
            Abbrev is first letter plus first cappital leather or digit after it.
        ''' 
        if name.startswith('server'): # strip 'server' from beginning
            name = name[6:]
        if name.startswith('validation'): # strip 'server' from beginning
            name = name[10:]
            
        abbrev = name[0]
        for letter in name[1:]:
            if letter.isupper() or letter.isdigit():
                abbrev += letter
                break
        return abbrev.upper()
    
    def get_state_title(self, state_id):
        return self.states_name[state_id] + ' - ' + self.states_desc[state_id]
    
    def get_states_title_for_row(self, row):
        title_list = []
        for state_id in self.state_list:
            if row[state_id]:
                title_list.append(self.get_state_title(state_id))
        if not title_list:
            title_list.append(self.get_state_title(0))
        return r'<br />'.join(title_list) 
    
    def transform_title(self, header, body):
        return 'header=[%s]body=[%s]' % (_(header), body) # body is already translated
    
    def make_content(self):
        state_table = self.compute_state_data()
        if self.owner_detail.history and len(state_table): # dont display history if state_table have no row
            self.content = []
            
            display_state_list = self.state_list[1:]
            self.tag = 'table'
            self.tattr_list = table.tattr_list
            self.cssc = 'state_table section_table'
            
            
            
            # header
            self.add(tr(th(_('Date')), [th(attr(cssc='state_header_cell', 
                                                title=self.transform_title(_('Status'), self.get_state_title(state_id))), 
                                           self.states_abbrev[state_id])
                                           for state_id in display_state_list
                                       ]))
            if state_table:
                # date rows
                for row in state_table:
                    tr_row = tr(th(attr(cssc='date_cell', title=self.transform_title(_('Statuses'), self.get_states_title_for_row(row))), row['row_date']))
                    for state_id in display_state_list:
                        state_on = row[state_id]
                        if state_on == True:
                            tr_row.add(td(attr(cssc='state_on', title=self.transform_title(_('Status'), self.get_state_title(state_id))), 'X'))
                        else:
                            tr_row.add(td(attr(title=self.transform_title(_('Status'), self.get_state_title(state_id)))))
                    self.add(tr_row)
        else:
            self.tag = 'table'
            self.tattr_list = table.tattr_list
            self.cssc = 'section_table'
            if len(state_table):
                self.add(tr(td(noesc(self.get_states_title_for_row(state_table[0])))))
            else:
                self.add(tr(td(self.get_state_title(0))))
                
        
        
            

class BaseNHDField(DField):
    ''' Parent class for NHDField. NHDField is based on value HistoryRecordList, but this field only
        switches between two fields according to history flag.
    '''
    def __init__(self, normal_field, history_field, *content, **kwd):
        self.normal_field = normal_field
        self.history_field = history_field
        self.current_field = None
        self._owner_detail = None
        self.displaying_history = False
        super(BaseNHDField, self).__init__(*content, **kwd)
        
    def _assign_current_field(self, new_current_field):
        self.current_field = new_current_field
        
    def value_from_data(self, data):
        value = data.get(self.name)
        if self.owner_detail.history:
            self._assign_current_field(self.history_field)
        else:
            self._assign_current_field(self.normal_field)
        return value
            
    def _set_value(self, value):
        if self.access:
            self._value = self.current_field.value = self.resolve_value(value)
            self.make_content()
        else:
            self._value = self.current_field.value = None
            self.make_content_no_access()
    def _get_value(self):
        if self.current_field:
            return self.current_field._value
        else:
            return fredtypes.Null()
    
    def _set_owner_detail(self, value):
        self._owner_detail = self.normal_field.owner_detail = self.history_field.owner_detail = value
    def _get_owner_detail(self):
        return self._owner_detail
    owner_detail = LateBindingProperty(_get_owner_detail, _set_owner_detail)
    
    def on_add(self):
        super(BaseNHDField, self).on_add()
        if self.current_field:
            self.current_field.parent_widget = self.parent_widget
            self.current_field.on_add() 
        
    def make_content(self):
        if self.access:
            self.content = []
            self.add(self.current_field)


class NHDField(BaseNHDField):
    """ Normal and History field combined in one. Depending of history flag of detail,
        one of them is used for render.
    """
    def value_from_data(self, data):
        value = data.get(self.name)
        
        if value is not None:
            if self.owner_detail.history and len(value) > 1 and not self.owner_detail.is_nested:
                self.displaying_history = True
                self.history_field.owner_detail = self.owner_detail
                self._assign_current_field(self.history_field)
                return value
            else:
                self.normal_field.owner_detail = self.owner_detail
                self._assign_current_field(self.normal_field)
                return from_any(value[0].value, True)
        else:
            self.normal_field.owner_detail = self.owner_detail
            self._assign_current_field(self.normal_field)
            return fredtypes.Null()
    
    
class CharNHDField(NHDField):
    def __init__(self, *content, **kwd):
        super(CharNHDField, self).__init__(CharDField(), HistoryDField(inner_field = CharDField()), *content, **kwd)

class DiscloseCharNHDField(NHDField):
    def __init__(self, disclose_name = None, *content, **kwd):
        super(DiscloseCharNHDField, self).__init__(DiscloseCharDField(), HistoryDField(inner_field=DiscloseCharDField()), *content, **kwd)
        self.disclose_name = disclose_name
    
    def merge_histories(self, hist1, hist2):
        ''' Merge histories of field and his dislose flag, If time is the same, 
            then histories are sorted/merged according to actionId 
            (if actionId is the same, then they are merged, otherwise sorted):
        '''
        all_dates = {} # key is (date, action_id), value is couple list of couple [hist_number, history record]
        
        for hist_num, hist in enumerate([hist1, hist2]):
            for rec in hist:
                from_date = recoder.corba_to_datetime(rec._from)
                if from_date: # from/to date can be empty, in that case we ignore it
                    key = (from_date, rec.actionId)
                    val = [hist_num, rec]
                    if all_dates.has_key(key):
                        all_dates[key].append(val)
                    else:
                        all_dates[key] = [val]
        
        new_hist = []
        last_hist_vals = {0: from_any(hist1[0].value, True), 
                          1: from_any(hist2[0].value, True)}
        last_hist_tos = {0: None,
                         1: None}
        
        for key, rec_list in sorted(all_dates.items()):
            for hist_num, rec in rec_list:
                last_hist_vals[hist_num] = from_any(rec.value, True)
                last_hist_tos[hist_num] = recoder.corba_to_datetime(rec.to)
            value = to_any([last_hist_vals[0], last_hist_vals[1]])
            action_id = rec_list[0][1].actionId
            _from = rec_list[0][1]._from
            
            to_dict = dict(
                [(hist_num, recoder.corba_to_datetime(rec.to)) for 
                    hist_num, rec in rec_list if 
                        recoder.corba_to_datetime(rec.to)])
            for hist_num in (0, 1):
                if not to_dict.has_key(hist_num):
                    to_dict[hist_num] = last_hist_tos[hist_num]
                if to_dict[hist_num] is None: # remove None
                    to_dict.pop(hist_num)
            if to_dict:
                to = recoder.datetime_to_corba(min(to_dict.values()))
            else: # all are NULL dates, take one of them
                to = rec_list[0][1].to
            new_rec = Registry.HistoryRecord(_from=_from, to=to, value=value, actionId = action_id)
            new_hist.append(new_rec)
        
        return list(reversed(new_hist))
    
    def value_from_data(self, data):
        # this 'if' cannot be in __init__ becouse name is not known in construction time:
        if self.disclose_name is None:
            self.disclose_name = 'disclose' + self.name[0].upper() + self.name[1:]

        value_name = data.get(self.name)
        if value_name is not None:
            value_disclose = data[self.disclose_name]
    
            value = self.merge_histories(value_name, value_disclose)
            return super(DiscloseCharNHDField, self).value_from_data({self.name: value})
        else:
            return super(DiscloseCharNHDField, self).value_from_data({})
