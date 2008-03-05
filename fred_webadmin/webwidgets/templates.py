#!/usr/bin/python
# -*- coding: utf-8 -*-

from gpyweb.gpyweb import div, span, p, a, b, attr, save, HTMLPage, hr, br, table, tr, th, td, img, form, input, h1, script
from adifforms import get_filter_forms_javascript
from fred_webadmin.translation import _
from fred_webadmin import config
 
class BaseTemplate(HTMLPage):
    def __init__(self, context = None):
        super(BaseTemplate, self).__init__(context)
        self.add_media_files('/css/base.css')
        print "pred body template"
        self.body.add(div(attr(id='container'),
                          save(self, 'container'),
                          div(attr(id='header'), save(self, 'header')),
                          #div(cssc='cleaner'),
                          div(attr(id='content_all'), save(self, 'content_all'), #cannot be "content", because of content attribute of gpyweb widgets
                              div(attr(id='columnwrap'), save(self, 'columnwrap'),
                                  div(attr(id='content-main'), save(self, 'main')))),
                          #div(cssc='cleaner'),
                          div(attr(id='footer'), save(self, 'footer'), '&copy; CZ.NIC z.s.p.o.')))
        print "za body template"
        
        
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
                                span('User: %s' % c.user.login), 
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
        self.main.add(p('disconnected, please ', a(attr(href='/login/'), 'log in'), 'again.'))
        
        

        
class BaseSiteMenu(BaseSite):
    def __init__(self, context = None):
        super(BaseSiteMenu, self).__init__(context)
        c = self.context
        if c.has_key('menu'):
            self.menu_container.add(div(attr(id='main-menu'), c.menu))
        if c.get('body_id'):
            self.body.add(attr(id=c.body_id))

#        self.main.add(div(attr(media_files=['/css/ext/css/ext-all.css', 
#                                            '/js/ext/ext-base.js', 
#                                            '/js/ext/ext-all.js', 
#                                            #'/js/itertable.js', 
#                                            '/js/smaz.js'
#                                           ])))

class FilterPage(BaseSiteMenu):
    def __init__(self, context = None):
        super(FilterPage, self).__init__(context)
        c = self.context
        if c.get('headline'):
            self.main.add(h1(c.headline))
        
        lang_code = config.lang[0:2]
        if lang_code == 'cs': # conversion between cs and cz identifier of lagnguage
            lang_code = 'cz'
        self.head.add(script(attr(type='text/javascript'), 
                             'scwLanguage = "%s"; //sets language of js_calendar' % lang_code,
                             'scwDateOutputFormat = "%s"; // set output format for js_calendar' % config.js_calendar_date_format))
                     
        if context.get('form'):
            self.main.add(c.form)
            #print "VKLADAM JS FORMU"
            forms_js = get_filter_forms_javascript()
            #print "a ten je konkretne", forms_js
            
            self.main.add(script(attr(type='text/javascript'), forms_js)) 
            
        if c.get('itertable'):
            itertable = c.itertable
            self.main.add(div(attr(id='div_for_itertable', cssc='extjs', media_files=['/css/ext/css/ext-all.css', '/js/ext/ext-base.js', '/js/ext/ext-all.js', '/js/itertable.js']), 'tady bude itertable'))

            self.main.add(br(), br())
            header = tr(attr(cssc="header"))
            for htext in itertable.header:
                header.add(td(htext))

            rows = [header]
            for irow in itertable:
                row = tr()
                for col in irow:
                    if col.get('icon'):
                        val = img(attr(src='/img/contenttypes/' + col['icon']))
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
                '%s: %s,' % (_('entries'), num_rows), 
                '%s: %s' % (_('total'), itertable.total_rows),
                br())
            
            # Pager
            if itertable.num_pages > 1:
                pageflip.add(div(
                    a(attr(cssc='pager-button', href='?page=%s' % itertable.first_page), '&laquo;'),
                    a(attr(cssc='pager-button', href='?page=%s' % itertable.prev_page), '&lsaquo;'),
#                    a(attr(cssc='pager-button', href='?page=%s' % itertable._number), itertable._number),
                    form(attr(style='display: inline;', method='GET'), input(attr(type='text', size='2', name='page', value=itertable.current_page))),
                    a(attr(cssc='pager-button', href='?page=%s' % itertable.next_page), '&rsaquo;'),
                    a(attr(cssc='pager-button', href='?page=%s' % itertable.last_page), '&raquo;')
                ))
            self.main.add(pageflip)
            



class DomainsDetail(BaseSiteMenu):
    def __init__(self, context = None):
        super(DomainsDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add('DOMAINSDETAIL', c.result.replace(u', ', u',<br />'))
        
    
class RegistrarsDetail(BaseSiteMenu):
    def __init__(self, context = None):
        super(RegistrarsDetail, self).__init__(context)
        c = self.context        
        if c.get('result'):
            self.add(c.result)
  
        self.body.add("""<form method="get">
<select name="pole" multiple="multiple">
<option value="1">jojo</option>
<option value="2">jo</option>
<option value="3">ne</option>
<option value="4">nene</option>
<input type="submit" value="OK"/>
</select>

<input name="bool" value="hodnota" type="checkbox" />

</form>""")


        
