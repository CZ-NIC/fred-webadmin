#!/usr/bin/python
# -*- coding: utf-8 -*-
from fred_webadmin.webwidgets.gpyweb.gpyweb import div, span, p, a, b, h2, h3, noesc, attr, save, HTMLPage, hr, br, table, tr, th, td, img, form, input, h1, script, pre
from fred_webadmin.webwidgets.forms.filterforms import get_filter_forms_javascript
from fred_webadmin.webwidgets.table import WIterTable
from fred_webadmin.translation import _
from fred_webadmin import config
from fred_webadmin.utils import get_current_url

from details import ContactDetailDiv, DomainDetailDiv, NSSetDetailDiv, ActionDetailDiv, RegistrarDetailDiv, PublicRequestDetailDiv, MailDetailDiv, InvoiceDetailDiv

class BaseTemplate(HTMLPage):
    def __init__(self, context = None):
        if context.get('doctype') is None:
            context['doctype'] = 'xhtml10strict'
        super(BaseTemplate, self).__init__(context)
        self.add_media_files('/css/base.css')
        self.body.add(div(attr(id='container'),
                          save(self, 'container'),
                          div(attr(id='header'), save(self, 'header')),
                          #div(cssc='cleaner'),
                          div(attr(id='content_all'), save(self, 'content_all'), #cannot be "content", because of content attribute of gpyweb widgets
                              div(attr(id='columnwrap'), save(self, 'columnwrap'),
                                  div(attr(id='content-main'), save(self, 'main')))),
                          #div(cssc='cleaner'),
                          div(attr(id='footer'), save(self, 'footer'), 
                              #'&copy; CZ.NIC z.s.p.o.'
                             )
                          ))
        
        
class BaseSite(BaseTemplate):
    def __init__(self, context = None):
        context = context or {}
        if not context.get('title'):
            context['title'] = 'Daphne'
        super(BaseSite, self).__init__(context)
        c = self.context
        self.add_media_files('/css/basesite.css')
        
        self.header.add(
            div(attr(id='branding'), save(self, 'branding'),
                div(attr(id='user_tools'), save(self, 'user_tools'))),
            div(attr(id='menu_container'), save(self, 'menu_container')),
        )
        self.branding.add(h1('Daphne'))
        
        if c.get('user') and c.get('corba_server'):
            self.user_tools.add(span('Server: %s' % c.corba_server),
                                '|',
                                span('User: %s(%s %s)' % (c.user.login, c.user.firstname, c.user.surname)), 
                                '|', 
                                a(attr(href="/logout"), 'Log out'))

        if c.get('main'):
            self.main.add(c.main)
            


class LoginPage(BaseSite):
    def __init__(self, context = None):
        super(LoginPage, self).__init__(context)
        c = self.context
        self.main.add(c.form)
        
class DisconnectedPage(BaseSite):
    def __init__(self, context = None):
        super(DisconnectedPage, self).__init__(context)
        self.main.add(p(_('Server disconnected, please '), 
                        a(attr(href='/login/?next=%s' % get_current_url()), 
                          _('log in')), ' again.'))

class NotFound404Page(BaseSite):
    def __init__(self, context = None):
        super(NotFound404Page, self).__init__(context)
        self.main.add(h1(_('Not found (404)')), 
                      p(_('Page not found'))
                     ) 
        
class BaseSiteMenu(BaseSite):
    def __init__(self, context = None):
        super(BaseSiteMenu, self).__init__(context)
        c = self.context
        if c.has_key('menu'):
            self.menu_container.add(div(attr(id='main-menu'), c.menu))
        if c.get('body_id'):
            self.body.add(attr(id=c.body_id))
        if c.get('headline'):
            self.main.add(h1(c.headline))
#        self.main.add(div(attr(media_files=['/css/ext/css/ext-all.css', 
#                                            '/js/ext/ext-base.js', 
#                                            '/js/ext/ext-all.js', 
#                                            #'/js/itertable.js', 
#                                            '/js/smaz.js'
#                                           ])))

class ErrorPage(BaseSiteMenu):
    def __init__(self, context = None):
        super(ErrorPage, self).__init__(context)
        c = self.context
        self.main.add(h1('Error:'))
        if c.has_key('message'):
            self.main.add(p(c.message))
    
class AllFiltersPage(BaseSiteMenu):
    ''' List of filters is displayed here. '''
    
    def __init__(self, context = None):
        super(AllFiltersPage, self).__init__(context)
        c = self.context
        if c.has_key('filters_list'):
            self.main.add(c['filters_list'])
            lang_code = config.lang[0:2]
            if lang_code == 'cs': # conversion between cs and cz identifier of lagnguage
                lang_code = 'cz'
            self.head.add(script(attr(type='text/javascript'), 
                                 'scwLanguage = "%s"; //sets language of js_calendar' % lang_code,
                                 'scwDateOutputFormat = "%s"; // set output format for js_calendar' % config.js_calendar_date_format))
        
    
class FilterPage(BaseSiteMenu):
    def __init__(self, context = None):
        super(FilterPage, self).__init__(context)
        c = self.context
        
        lang_code = config.lang[0:2]
        if lang_code == 'cs': # conversion between cs and cz identifier of lagnguage
            lang_code = 'cz'
        self.head.add(script(attr(type='text/javascript'), 
                             'scwLanguage = "%s"; //sets language of js_calendar' % lang_code,
                             'scwDateOutputFormat = "%s"; // set output format for js_calendar' % config.js_calendar_date_format))
                     
        if context.get('form') and (config.debug or not c.get('itertable')):
            self.main.add(c.form)
            self.main.add(script(attr(type='text/javascript'), 'Ext.onReady(function () {addFieldsButtons()})')) 
            
            #print "VKLADAM JS FORMU"
            #import cProfile
            #cProfile.runctx('forms_js = get_filter_forms_javascript()', globals(), locals(), 'prof2')

            #forms_js = get_filter_forms_javascript()
            #self.main.add(script(attr(type='text/javascript'), forms_js)) 
        
        if c.get('result'):
            self.main.add(p(c['result']))
        
        if c.get('itertable'):
            
            itertable = c.itertable
            self.main.add(div(attr(id='div_for_itertable', cssc='extjs', 
                                   media_files=['/css/ext/css/ext-all.css', 
#                                                '/js/MochiKit/MochiKit.js',
                                                '/js/logging.js', 
                                                '/js/ext/ext-base.js', 
                                                '/js/ext/ext-all.js', 
                                                '/js/itertable.js'])))
            self.main.add(p(_('Table_as'), a(attr(href='?txt=1'), 'TXT'), ',', a(attr(href='?csv=1'), 'CSV')))
            
            if config.debug:
                self.main.add(br(), br())
                header = tr(attr(cssc="header"))
                for htext in itertable.header:
                    header.add(td(htext))
                
                rows = [header]
                for irow in itertable:
                    row = tr()
                    for col in irow:
                        if col.get('icon'):
                            val = img(attr(src=col['icon']))
                        else:
                            val = col['value']
                        
                        if col.get('url'):
                            val = a(attr(href=col['url']), val)
                        
                        row.add(td(attr(cssc=col.get('cssc')), val))
                    rows.append(row)


                self.main.add(table(attr(id='objectlist', media_files='/css/objectlist.css'), rows))
                
                # Numbers of entries 
                if itertable.total_rows > itertable.num_rows:
                    num_rows = span(attr(cssc='warning'), itertable.num_rows)
                else:
                    num_rows = itertable.num_rows
                pageflip = span(
                    '%s: %s,' % (_('Number_of_pages'), itertable.last_page),
                    '%s: ' % _('entries'), num_rows, ',', 
                    '%s: %s' % (_('total'), itertable.total_rows),
                    br())
                
                # Pager
                if itertable.num_pages > 1:
                    pageflip.add(div(
                        a(attr(cssc='pager-button', href='?page=%s' % itertable.first_page), noesc('&laquo;')),
                        a(attr(cssc='pager-button', href='?page=%s' % itertable.prev_page), noesc('&lsaquo;')),
    #                    a(attr(cssc='pager-button', href='?page=%s' % itertable._number), itertable._number),
                        form(attr(style='display: inline;', method='GET'), input(attr(type='text', size='2', name='page', value=itertable.current_page))),
                        a(attr(cssc='pager-button', href='?page=%s' % itertable.next_page), noesc('&rsaquo;')),
                        a(attr(cssc='pager-button', href='?page=%s' % itertable.last_page), noesc('&raquo;'))
                    ))
                self.main.add(pageflip)
            
            #self.main.add(WIterTable(itertable))



class DomainDetail(BaseSiteMenu):
    def __init__(self, context = None):
        super(DomainDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(DomainDetailDiv(context))
            if config.debug:
                self.main.add('DOMAINDETAIL:', div(attr(style='width: 1024; overflow: auto;'), pre(unicode(c.result).replace(u', ', u',\n'))))
                
                
class ContactDetail(BaseSiteMenu):
    def __init__(self, context = None):
        super(ContactDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(ContactDetailDiv(context))
            if config.debug:            
                self.main.add('ContactDETAIL:', pre(unicode(c.result).replace(u', ', u',\n')))

class NSSetDetail(BaseSiteMenu):
    def __init__(self, context = None):
        super(NSSetDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(NSSetDetailDiv(context))
            if config.debug:
                self.main.add('NSSetDETAIL:', pre(unicode(c.result).replace(u', ', u',\n')))

class ActionDetail(BaseSiteMenu):
    def __init__(self, context = None):
        super(ActionDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(ActionDetailDiv(context))
            if config.debug:
                self.main.add('ACTIONDETAIL:', pre(unicode(c.result).replace(u', ', u',\n')))
        
    
class RegistrarDetail(BaseSiteMenu):
    def __init__(self, context = None):
        super(RegistrarDetail, self).__init__(context)
        c = self.context        
        if c.get('result'):
            self.main.add(RegistrarDetailDiv(context))
            self.main.add(p(a(attr(href=u'../edit/?id=' + unicode(c.result.id)), _('Edit'))))
            if config.debug:
                self.main.add('RegistrarDETAIL:', pre(unicode(c.result).replace(u', ', u',\n')))
            
class PublicRequestDetail(BaseSiteMenu):
    def __init__(self, context = None):
        super(PublicRequestDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(PublicRequestDetailDiv(context))
            if config.debug:
                self.main.add('PublicRequestSDETAIL:', pre(unicode(c.result).replace(u', ', u',\n')))
                
  
class MailDetail(BaseSiteMenu):
    def __init__(self, context = None):
        super(MailDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(MailDetailDiv(context))
            if config.debug:
                self.main.add('MailDETAIL:', div(attr(style='width: 1024px; overflow: auto;'), pre(unicode(c.result).replace(u', ', u',\n'))))

class InvoiceDetail(BaseSiteMenu):
    def __init__(self, context = None):
        super(InvoiceDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(InvoiceDetailDiv(context))
            if config.debug:
                self.main.add('InvoiceDETAIL:', pre(unicode(c.result).replace(u', ', u',\n')))
                
                
class EditPage(BaseSiteMenu):
    def __init__(self, context = None):
        super(EditPage, self).__init__(context)
        c = self.context
        if c.get('form'):
            self.main.add(c.form)

class RegistrarEdit(EditPage):
    pass
            


class DigPage(BaseSiteMenu):
    def __init__(self, context = None):
        super(DigPage, self).__init__(context)
        c = self.context
        self.main.add(h2(_('dig_query')))
        if c.get('handle'):
            self.main.add(h3(_('Domain'), c.handle))
        if c.get('dig'):
            self.main.add(pre(c.dig))
