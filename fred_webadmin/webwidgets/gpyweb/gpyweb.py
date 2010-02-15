#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, types, time
from cgi import escape
import fred_webadmin.nulltype as fredtypes

class GPyWebError(Exception):
    pass

class attr(object):
    #_is_tag_attr = True
    
    def __init__(self, **kwd):
        '''To can specify list of parameters of tag as first parametr of widget.add(...) call'''
        self.kwd = kwd
        
class tagid(object):
    def __init__(self, name):
        '''To mark tag to be accesible through parenttag.name or parenttag[name]'''
        self.name = name

class save(object):
    '''To save widget into another widget under a specified name.'''
    def __init__(self, parent_widget, name):
        if type(name) in types.StringTypes:
            self.parent_widget = parent_widget #this doesn't have to be widget
            self.name = name
        else:
            raise Exception
        
class noesc(object):
    '''String inside this objec will not be escaped'''
    def __init__(self, value):
        self.value = value

class SubscriptableType(type):
    ''' Metaclass, which allows create webwidget using call like div['content'] instead 
        and will work as constructor (e.g. div('content'))
    '''
    def __getitem__(cls, content):
        new_obj = cls.__new__(cls)
        new_obj.__init__()
        return new_obj[content]
                
class WebWidget(object):
    '''Base class for all web widgets'''
    
    __metaclass__ = SubscriptableType
    
#    # normal attributes are not rendered to html output
    # normal (class) attributes, that can be passed through attr object or as kwd argument (normally only tag attributes can be passed using attr object)
    normal_attrs = ['tag', 'enclose_content', 'empty_tag_as_xml', 'media_files'] 
    tattr_list = []
    
    # some attributes need to be translated before render, because they have no format of python attributes
    attr_translation = {
        u'xmllang': u'xml:lang',
        u'httpequiv': u'http-equiv',
        u'cssc': u'class',
        u'for_id': u'for',
    }
    
    indent_char = u'\t'
    delimiter_char = u'\n'
    
    enclose_content = False
    empty_tag_as_xml = True
    #- True: 
    # <a>content</a>
    #
    #- False: 
    # <p>
    #     content
    # </p>

    
    
    def __init__(self, *content, **kwd):
        self.__dict__['tattr'] = {} # attributes, that will be rendered into tag as attribute (eg. <a href="/">...)
        self.__dict__['content'] = [] # To not pydev(or pylint) complain about assigning to undefined membet 'attr'
        self.parent_widget = None
        
        self.tag = self.__class__.__name__
    
        self._root_widget = self # root webwidget (usualy hmtl tag)
        self.media_files = [] # list of media files, which is rendered in head tag of HTMLPage, if this element is rendered in HTMLPage
        # allows content to be added via the 'content' keyword, which
        # provides an alternative to using the 'attr' class
        content = list(content) # convert tuple to list
        if kwd.has_key('content'):
            content_kwd = kwd['content']
            if isinstance(content_kwd, (types.ListType, types.TupleType)):
                content += content_kwd
            else:
                content += [content_kwd]
            del kwd['content']
        for con in content:
            self.add(con)
    
        # Allow a 'parent' keyword, which auto-adds this tag to a parent tag
        if kwd.has_key('parent'):
            parent = kwd['parent']
            del kwd['parent']
            parent.add(self)
 
#        # save normal attributes as normal object attributes
        # save tag attributes into self.tattr and some of normal attributes normally 
        for key, val in kwd.items():
            if key in self.tattr_list:
                self.tattr[key] = val
                kwd.pop(key)
            elif key in self.normal_attrs:
                self.__setattr__(key, val)
                kwd.pop(key)
                
        if kwd:
            raise GPyWebError(u'Attributes "%s" are not allowed in tag %s (class %s)' % (kwd, self.tag, self.__class__.__name__))

    def _set_root_widget(self, value):
        "Set root_widget and recursively for all descendants (only if value is changed)"
        if self._root_widget != value:
            for con in self.content:
                if isinstance(con, WebWidget): 
                    con.root_widget = value
        self._root_widget = value
    def _get_root_widget(self):
        return self._root_widget
    root_widget = property(_get_root_widget, _set_root_widget)
        
        
    def __getattr__(self, name):
        if name in ['__reduce__', '__getstate__', '__setstate__', '__module__', '__getinitargs__', '__getnewargs__', '__deepcopy__', 
                    'tatr' 'content']:
            raise AttributeError, name
        if self.tattr.has_key(name):
            return self.tattr[name]
        else:
            # must be using __dict__ because if descendant of WebWidget overrides __getattr__ method,
            # there would be maximum recursion depth exceeded error raised
            for con in self.__dict__['content']: 
                if isinstance(con, WebWidget):
                    try:
                        tname = getattr(con, 'tagid')
                        if tname == name:
                            return con
                    except AttributeError:
                        pass
        raise AttributeError(u'__getattr__ try to access non-existend attribute "%s" of object "%s"' % (name, unicode(self.__repr__())))

    def __setattr__(self, name, value):
        if name == 'content':
            if value == None or value == fredtypes.Null():
                super(WebWidget, self).__setattr__('content', [])
            else:
                super(WebWidget, self).__setattr__('content', list(value))
        elif name in self.tattr_list:
            self.tattr[name] = value
        else:
            super(WebWidget, self).__setattr__(name, value)
    
    def __str__(self):
        return self.render()
    
    def __unicode__(self):
        return self.__str__()
    
    def on_add(self):
        ''' This method is called everytime when WebWidget is added to another webwidget 
            (after parent_widget and root_widget attributes was assignet)
        '''
        pass
        
    def add(self, *content, **kwd):
        for con in content:
            if isinstance(con, WebWidget):
                con.parent_widget = self
                con.root_widget = self.root_widget
                con.on_add()
                self.content.append(con)
            elif isinstance(con, save):
                # this must be done over __dict__, because if it would use
                #__setattr__, it would become tattr attribute
                con.parent_widget.__setattr__(con.name, self) 
            elif isinstance(con, tagid):
                self.__setattr__('tagid', con.name)
            elif isiterable(con):
                for inner_con in con:
                    self.add(inner_con)
            elif isinstance(con, attr):
                for key, val in con.kwd.items():
                    if key in self.tattr_list:
                        self.tattr[key] = val
                    elif key in self.normal_attrs:
                        self.__setattr__(key, val)
                    else:
                        raise GPyWebError(
                            u"""Attribute %s is not allowed for element"""
                            """ %s (class %s)""" % (key, self.tag, 
                            self.__class__.__name__))
            elif con != None:
                self.content.append(con)
                
    def set_tattr(self, *talist, **kwd):
        for tag_attr in talist:
            if isinstance(tag_attr, attr):
                kwd.update(tag_attr.kwd)
            elif isinstance(tag_attr, types.DictType):
                kwd.update(tag_attr)
        for key, val in kwd.items():
            if key in self.tattr_list:
                self.tattr[key] = val
            elif key in self.normal_attrs:
                self.__setattr__(key, val)
            else:
                raise GPyWebError(u'Attribute %s is not allowed for element %s (class %s)' % (key, self.tag, self.__class__.__name__))
            
    def render_tattr(self):
        '''Returns space-separated list of widget's tag attributes'''
        rstr = ''
        for key, val in self.tattr.items():
            if val is not None and val != fredtypes.Null():
                val = escape(unicode(val), quote=True)
                if key in self.attr_translation.keys():
                    rstr += u' %s="%s"' % (self.attr_translation[key], val)
                else:    
                    rstr += u' %s="%s"' % (key, val)
        return rstr
            

    def render(self, indent_level = 0):
        if self.media_files and self.root_widget and \
          isinstance(self.root_widget, HTMLPage):
            self.root_widget.add_media_files(self.media_files)
            
        rstr = ''
        
        if self.tag:
            if (self.parent_widget and not self.parent_widget.enclose_content) or not self.parent_widget:
                rstr += indent_level * self.indent_char
            rstr += u'<' + self.tag
            rstr += self.render_tattr()
            if len(self.content) or not self.empty_tag_as_xml:
                rstr += u'>'
            else:
                rstr += u' />'
            if not self.enclose_content:
                rstr += self.delimiter_char
        
        rstr += self.render_content(indent_level + 1)
        
        if self.tag and (len(self.content) > 0 or not self.empty_tag_as_xml):
            if not self.enclose_content:
                rstr += indent_level * self.indent_char
            rstr += u'</' + self.tag + u'>'
            if self.parent_widget:
                if not self.parent_widget.enclose_content :
                    rstr += self.delimiter_char
            else:
                rstr += self.delimiter_char
                
        return rstr
        
    def render_content(self, indent_level = 0):
        rstr = ''
        
        for con in self.content:
            if con is None:
                continue
            if isinstance(con, WebWidget):
                rstr += con.render(indent_level)
            elif isinstance(con, types.StringTypes):
                if not self.enclose_content:
                    rstr += indent_level * self.indent_char
                rstr += escape(con)
                if not self.enclose_content:
                    rstr += self.delimiter_char
            elif isinstance(con, (types.ListType, types.TupleType)):
                for item in con:
                    if item is not None:
                        rstr += unicode(item) # strings in list are not escaped!
            elif isinstance(con, noesc):
                if not self.enclose_content:
                    rstr += indent_level * self.indent_char
                rstr += con.value # value will not be escaped!
                if not self.enclose_content:
                    rstr += self.delimiter_char
            else:
                con = unicode(con)
                if not self.enclose_content:
                    rstr += indent_level * self.indent_char
                rstr += con
                if not self.enclose_content:
                    rstr += self.delimiter_char
                    
        return rstr
    
    def __getitem__(self, content):
        if isinstance(content, (types.TupleType, types.ListType)):
            self.add(*content)
        else:
            self.add(content)
        return self


class notag(WebWidget):
    def __init__(self, *content, **kwd):
        super(notag, self).__init__(*content, **kwd)
        self.tag = ''

class pre(WebWidget):
    enclose_content = True    
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'xml:space']

class em(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class code(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class h2(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class h3(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class h1(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class h6(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class dl(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class h4(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class h5(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class area(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'accesskey', 'tabindex', 'onfocus', 'onblur', 'shape', 'coords', 'href', 'nohref', 'alt']

class meta(WebWidget):
    tattr_list=['lang', 'xmllang', 'dir', 'id', 'httpequiv', 'name', 'content', 'scheme']

class table(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'summary', 'width', 'border', 'frame', 'rules', 'cellspacing', 'cellpadding']

class dfn(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class label(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'for_id', 'accesskey', 'onfocus', 'onblur']

class select(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'name', 'size', 'multiple', 'disabled', 'tabindex', 'onfocus', 'onblur', 'onchange']

class noscript(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class style(WebWidget):
    tattr_list=['lang', 'xmllang', 'dir', 'id', 'type', 'media', 'title', 'xml:space']

class strong(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class span(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class sub(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class img(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'src', 'alt', 'longdesc', 'height', 'width', 'usemap', 'ismap']

class title(WebWidget):
    enclose_content = True
    tattr_list=['lang', 'xmllang', 'dir', 'id']

class bdo(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'lang', 'xmllang', 'dir']

class tr(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'align', 'char', 'charoff', 'valign']

class tbody(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'align', 'char', 'charoff', 'valign']

class param(WebWidget):
    tattr_list=['id', 'name', 'value', 'valuetype', 'type']

class li(WebWidget):
    enclose_content = True
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class acronym(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class html(WebWidget):
    tattr_list=['lang', 'xmllang', 'dir', 'id', 'xmlns']

class caption(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class tfoot(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'align', 'char', 'charoff', 'valign']

class th(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'abbr', 'axis', 'headers', 'scope', 'rowspan', 'colspan', 'align', 'char', 'charoff', 'valign']

class sup(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class var(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class input(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'accesskey', 'tabindex', 'onfocus', 'onblur', 'type', 'name', 'value', 'checked', 'disabled', 'readonly', 'size', 'maxlength', 'src', 'alt', 'usemap', 'onselect', 'onchange', 'accept']

class td(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'abbr', 'axis', 'headers', 'scope', 'rowspan', 'colspan', 'align', 'char', 'charoff', 'valign']

class samp(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class cite(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class thead(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'align', 'char', 'charoff', 'valign']

class body(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'onload', 'onunload']

class map(WebWidget):
    tattr_list=['lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'id', 'cssc', 'style', 'title', 'name']

class head(WebWidget):
    tattr_list=['lang', 'xmllang', 'dir', 'id', 'profile']

class blockquote(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'cite']

class fieldset(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class option(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'selected', 'disabled', 'label', 'value']

class form(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'action', 'method', 'enctype', 'onsubmit', 'onreset', 'accept', 'accept-charset']

class hr(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class big(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class dd(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class object(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'declare', 'csscid', 'codebase', 'data', 'type', 'codetype', 'archive', 'standby', 'height', 'width', 'usemap', 'name', 'tabindex']

class base(WebWidget):
    tattr_list=['href', 'id']

class link(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'charset', 'href', 'hreflang', 'type', 'rel', 'rev', 'media']

class kbd(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class br(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title']

class address(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class optgroup(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'disabled', 'label']

class dt(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class ins(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'cite', 'datetime']

class b(WebWidget):
    enclose_content = True
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class legend(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'accesskey']

class abbr(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class a(WebWidget):
    enclose_content = True
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'accesskey', 'tabindex', 'onfocus', 'onblur', 'charset', 'type', 'name', 'href', 'hreflang', 'rel', 'rev', 'shape', 'coords']

class ol(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class textarea(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'accesskey', 'tabindex', 'onfocus', 'onblur', 'name', 'rows', 'cols', 'disabled', 'readonly', 'onselect', 'onchange']

class colgroup(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'span', 'width', 'align', 'char', 'charoff', 'valign']

class i(WebWidget):
    enclose_content = True
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class button(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'accesskey', 'tabindex', 'onfocus', 'onblur', 'name', 'value', 'type', 'disabled']

class script(WebWidget):
    tattr_list=['id', 'charset', 'type', 'src', 'defer', 'xml:space']

class col(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'span', 'width', 'align', 'char', 'charoff', 'valign']

class q(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup', 'cite']

class p(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class small(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class div(WebWidget):
    empty_tag_as_xml = False # because <div /> is treated by browsers as <div>, so then unclosed divs happend and layout is broken
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class tt(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']

class ul(WebWidget):
    tattr_list=['id', 'cssc', 'style', 'title', 'lang', 'xmllang', 'dir', 'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup']



class CSSInclude(WebWidget):
    def __init__(self, css_file):
        super(CSSInclude, self).__init__(css_file)
        self.tag = 'link'
        
        self.add(attr(href=css_file, rel="stylesheet", type="text/css"))

class JSInclude(WebWidget):
    def __init__(self, js_file):
        super(JSInclude, self).__init__(js_file)
        self.tag = 'script'
        self.enclose_content=True
        #must contain empty string because browser take <script /> as if it was <script> and waiting for </scrpt>:        
        self.add(attr(src=js_file, type="text/javascript"), '', )
        
GPYWEB_REPLACE_ME_WITH_MEDIA = 'GPYWEB_REPLACE_ME_WITH_MEDIA'
class Media(WebWidget):
    def __init__(self, media_files, *content, **kwd):
        super(Media, self).__init__(*content, **kwd)
        self.tag = None
        
        if isinstance(media_files, types.StringTypes):
            self.media_files = [media_files] #set([media_files])
        elif isiterable(media_files):
            self.media_files = media_files #set(media_files)
        else:
            self.media_files = [] #set()

    def render_after(self):
        rstr = ''
        for media_file in self.media_files:
            if media_file.endswith('.css'):
                rstr += self.indent_level * self.indent_char
                rstr += unicode(link(href=media_file, rel="stylesheet", type="text/css"))
            else:
                rstr += self.indent_level * self.indent_char
                #must contain empty string because browser take <script /> as if it was <script> and waiting for </scrpt>:        
                rstr += unicode(script('', src=media_file, type="text/javascript", enclose_content=True))
        return rstr
        
            
    def render(self, indent_level = 0):
        self.indent_level = indent_level
        return GPYWEB_REPLACE_ME_WITH_MEDIA
        rstr = ''
        for media_file in self.media_files:
            if media_file.endswith('.css'):
                rstr += indent_level * self.indent_char
                rstr += unicode(link(href=media_file, rel="stylesheet", type="text/css"))
            else:
                rstr += indent_level * self.indent_char
                #must contain empty string because browser take <script /> as if it was <script> and waiting for </scrpt>:        
                rstr += unicode(script('', src=media_file, type="text/javascript", enclose_content=True))
        return rstr
                
            
class DictLookup(dict):
    def __getattr__(self, name):
        return self[name]
    def __setattr__(self, name, value):
        self[name] = value
    def __getstate__(self):
        pass


class HTMLPage(html):
    def __init__(self, context=None):
        super(HTMLPage, self).__init__()
        #self.normal_attrs += ['context', 'doctype', '_media', 'head', 'title_tag', 'body']
        self.context = context = DictLookup(context or {})
        self.tag = 'html'
        media_files = context.get('media_files')
        
        title_str = context.get('title') or u'Title'
        charset = context.get('charset') or u'utf-8'
        lang = context.get('lang') or u'en'
        
        doctype = context.get('doctype')
        if doctype == 'xhtml10strict':
            self.doctype = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
        elif doctype == 'xhtml11':
            self.doctype = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">'
        elif doctype == 'html4':
            self.doctype = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd" >'
        else:
            self.doctype = doctype or ''
        
        self.head = None
        self._media = None
        self.title_tag = None
        self.body = None
        
        self.add(attr(xmlns = "http://www.w3.org/1999/xhtml", xmllang=lang),
                 head(save(self, 'head'),
                      meta(attr(httpequiv = "Content-Type", content="text/html; charset=%s" % charset)),
                      title(save(self, 'title_tag'),
                            title_str
                           ),
                      Media(media_files, save(self, '_media')),
                     ),
                 body(save(self, 'body'))
                 )
                
    def render(self, indent_level = 0):
        return self.doctype + super(HTMLPage, self).render(indent_level).replace(GPYWEB_REPLACE_ME_WITH_MEDIA, self._media.render_after(), 1)    
    def add_media_files(self, media_files):
        if isinstance(media_files, types.StringTypes):
            media_files = [media_files]
        for media_file in media_files:
            if media_file not in self._media.media_files:
                self._media.media_files.append(media_file)

def isiterable(par):
    # we don't want to iterate over string characters
    if isinstance(par, types.StringTypes):
        return False

    try:
        iter(par)
        return True
    except TypeError:
        return False
        
