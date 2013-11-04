#!/usr/bin/python
# -*- coding: utf-8 -*-
import simplejson
from fred_webadmin.webwidgets.gpyweb.gpyweb import (
    div, span, p, a, b, button, h2, h3, noesc, attr, save, HTMLPage, hr, br, table,
    tr, th, td, img, form, label, input, h1, ul, li, script, pre, textarea, tagid, notag)
from fred_webadmin.translation import _
from fred_webadmin import config
from fred_webadmin.utils import get_current_url, append_getpar_to_url

from fred_webadmin.webwidgets.details import adifdetails
from fred_webadmin.webwidgets.forms import editforms

class BaseTemplate(HTMLPage):
    def __init__(self, context=None):
        if context.get('doctype') is None:
            context['doctype'] = 'xhtml10strict'
        super(BaseTemplate, self).__init__(context)
        self.add_media_files('/css/base.css')
        self.body.add(div(attr(id='container'),
                          save(self, 'container'),
                          div(attr(id='header'), save(self, 'header')),
                          div(attr(id='content_all'), save(self, 'content_all'), #cannot be "content", because of content attribute of gpyweb widgets
                              div(attr(id='columnwrap'), save(self, 'columnwrap'),
                                  div(attr(id='content-main'), save(self, 'main')))),
                          div(attr(id='footer'), save(self, 'footer'))
                          ))


class BaseSite(BaseTemplate):
    def __init__(self, context=None):
        context = context or {}

        if not context.get('title'):
            context['title'] = 'Daphne'
            if context.get('user') and context.get('corba_server'):
                context['title'] += ' - %s' % context.get('corba_server')

        super(BaseSite, self).__init__(context)
        c = self.context

        self.add_media_files('/css/basesite.css')
        self.header.add(
            div(attr(id='branding'), save(self, 'branding'),
                div(attr(id='user_tools'), save(self, 'user_tools'))),
            div(
                div(attr(id='menu_container'), save(self, 'menu_container')),
                div(attr(id='right_menu_container'), save(self, 'right_menu_container'),
                )
            )
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
    def __init__(self, context=None):
        super(LoginPage, self).__init__(context)
        c = self.context
        self.main.add(c.form)

class DisconnectedPage(BaseSite):
    def __init__(self, context=None):
        super(DisconnectedPage, self).__init__(context)
        self.main.add(p(_('Server disconnected, please '),
                        a(attr(href='/login/?next=%s' % get_current_url()),
                          _('log in')), ' again.'))

class NotFound404Page(BaseSite):
    def __init__(self, context=None):
        super(NotFound404Page, self).__init__(context)
        self.main.add(h1(_('Not found (404)')),
                      p(_('Page not found'))
                     )

class BaseSiteMenu(BaseSite):
    def __init__(self, context=None):
        super(BaseSiteMenu, self).__init__(context)
        c = self.context
        if c.has_key('menu'):
            self.menu_container.add(div(attr(id='main-menu'), c.menu))
        if c.get('body_id'):
            self.body.add(attr(id=c.body_id))
        if c.get('headline'):
            self.main.add(h1(c.headline))
        self.right_menu_container.add(
            input(save(self, 'history_checkbox'),
                  attr(media_files=['/js/history_button.js', '/js/ext/ext-base.js', '/js/ext/ext-all.js',
                                    '/js/jquery-2.0.3.min.js'],
                       id='history_checkbox',
                       type='checkbox', onchange='setHistory(this)')),
                  label(attr(for_id='history_checkbox'), _('history'))
        )
        if c.history:
            self.history_checkbox.checked = ['', 'checked'][c.history]


class ErrorPage(BaseSiteMenu):
    def __init__(self, context=None):
        super(ErrorPage, self).__init__(context)
        c = self.context
        self.main.add(h1('Error:'))
        if c.has_key('message'):
            self.main.add(p(c.message))

class AllFiltersPage(BaseSiteMenu):
    ''' List of filters is displayed here. '''

    def __init__(self, context=None):
        super(AllFiltersPage, self).__init__(context)
        c = self.context
        if c.has_key('filters_list'):
            self.main.add(c['filters_list'])
            lang_code = config.lang[:2]
            if lang_code == 'cs': # conversion between cs and cz identifier of lagnguage
                lang_code = 'cz'
            self.head.add(script(attr(type='text/javascript'),
                                 'scwLanguage = "%s"; //sets language of js_calendar' % lang_code,
                                 'scwDateOutputFormat = "%s"; // set output format for js_calendar' % config.js_calendar_date_format))


class FilterPage(BaseSiteMenu):
    def __init__(self, context=None):
        super(FilterPage, self).__init__(context)
        c = self.context

        lang_code = config.lang[0:2]
        if lang_code == 'cs': # conversion between cs and cz identifier of lagnguage
            lang_code = 'cz'
        self.head.add(script(attr(type='text/javascript'),
                             'scwLanguage = "%s"; //sets language of js_calendar' % lang_code,
                             'scwDateOutputFormat = "%s"; // set output format for js_calendar' % config.js_calendar_date_format))

        if context.get('form') and (config.debug or not c.get('itertable') or c.get('show_form')):
            self.main.add(c.form)
            self.main.add(script(attr(type='text/javascript'), 'Ext.onReady(function () {addFieldsButtons()})'))
        else:
            self.main.add(a(attr(href=append_getpar_to_url(add_par_dict={'load': 1, 'show_form': 1})), _('Modify filter')))

        if c.get('result'):
            self.main.add(p(c['result']))

        if c.get('witertable'):
            if c.get('blocking_mode'):
                self.main.add(h1(attr(id='blocking_text'), _('Administrative blocking')))
            self.main.add(c.witertable)
            if not c.get('blocking_mode'):
                self.main.add(p(_('Table_as'), a(attr(href='?txt=1'), 'TXT'), ',', a(attr(href='?csv=1'), 'CSV')))

        if c.get("display_jump_links"):
            # Display the 'previous' and 'next' links (they auto-submit
            # the form to display results for the prev./next time interval).
            jump_links_info = c.get("display_jump_links")
            self.main.add(div(
                a(attr(
                    title="Jumps to the previous time period.",
                    href=(jump_links_info['url'] +
                        'filter/?jump_prev=1&field_name=%s' %
                        jump_links_info['field_name'])),
                  "prev"),
                a(attr(
                    title="Jumps to the next time period.",
                    href=(jump_links_info['url'] +
                        'filter/?jump_next=1&field_name=%s' %
                        jump_links_info['field_name'])),
                  "next")))

        if c.get('blocking_possible') and not c.get('blocking_mode'):
            self.main.add(p(a(attr(href='./blocking_start/'), _('Administrative blocking'))))



class DetailPage(BaseSiteMenu):
    @classmethod
    def get_object_name(cls):
        return cls.__name__[:-len('Detail')].lower()

class DomainDetail(DetailPage):
    def __init__(self, context=None):
        super(DomainDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(h1(_('Detail_of_%s' % self.get_object_name())))
            self.main.add(adifdetails.DomainDetail(c.result, c.history))
            if config.debug:
                self.main.add('DOMAINDETAIL:', div(attr(style='width: 1024px; overflow: auto;'), pre(unicode(c.result).replace(u', ', u',\n'))))


class ContactDetail(DetailPage):
    def __init__(self, context=None):
        super(ContactDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(h1(_('Detail_of_%s' % self.get_object_name())))
            self.main.add(adifdetails.ContactDetail(c.result, c.history))
            if config.debug:
                self.main.add('ContactDETAIL:', pre(unicode(c.result).replace(u', ', u',\n')))

class NSSetDetail(DetailPage):
    def __init__(self, context=None):
        super(NSSetDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(h1(_('Detail_of_%s' % self.get_object_name())))
            self.main.add(adifdetails.NSSetDetail(c.result, c.history))
            if config.debug:
                self.main.add('NSSetDETAIL:', pre(unicode(c.result).replace(u', ', u',\n')))

class KeySetDetail(DetailPage):
    def __init__(self, context=None):
        super(KeySetDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(h1(_('Detail_of_%s' % self.get_object_name())))
            self.main.add(adifdetails.KeySetDetail(c.result, c.history))
            if config.debug:
                self.main.add('KeySetDETAIL:', pre(unicode(c.result).replace(u', ', u',\n')))

class RegistrarDetail(DetailPage):
    def __init__(self, context=None):
        super(RegistrarDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(h1(_('Detail_of_%s' % self.get_object_name())))
            self.main.add(adifdetails.RegistrarDetail(c.result, c.history))
            if config.debug:
                self.main.add('RegistrarDETAIL:', pre(unicode(c.result).replace(u', ', u',\n')))

class PublicRequestDetail(DetailPage):
    def __init__(self, context=None):
        super(PublicRequestDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(h1(_('Detail_of_%s' % self.get_object_name())))
            self.main.add(adifdetails.PublicRequestDetail(c.result, c.history))
            if config.debug:
                self.main.add('PublicRequestSDETAIL:', pre(unicode(c.result).replace(u', ', u',\n')))


class MailDetail(DetailPage):
    def __init__(self, context=None):
        super(MailDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(h1(_('Detail_of_%s' % self.get_object_name())))
            self.main.add(adifdetails.MailDetail(c.result, c.history))
            if config.debug:
                self.main.add('MailDETAIL:', div(attr(style='width: 1024px; overflow: auto;'), pre(unicode(c.result).replace(u', ', u',\n'))))


class InvoiceDetail(DetailPage):
    def __init__(self, context=None):
        super(InvoiceDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(h1(_('Detail_of_%s' % self.get_object_name())))
            self.main.add(adifdetails.InvoiceDetail(c.result, c.history))
            if config.debug:
                self.main.add('InvoiceDETAIL:', pre(unicode(c.result).replace(u', ', u',\n')))


class LoggerDetail(DetailPage):
    def __init__(self, context=None):
        super(LoggerDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(h1(_('Detail_of_%s' % self.get_object_name())))
            self.main.add(adifdetails.LoggerDetail(c.result, c.history))
            if config.debug:
                self.main.add('LoggerDETAIL:', pre(unicode(c.result).replace(u', ', u',\n')))


class BankStatementDetail(DetailPage):
    def __init__(self, context=None):
        super(BankStatementDetail, self).__init__(context)
        c = self.context
        if c.get('detail'):
            self.main.add(h1(_("Detail of payment")))
            self.main.add(adifdetails.BankStatementDetail(c.detail, c.history))
            if config.debug:
                self.main.add('BankStatementDETAIL:', pre(unicode(c.detail).replace(u', ', u',\n')))


class BankStatementDetailWithPaymentPairing(DetailPage):
    def __init__(self, context=None):
        super(BankStatementDetailWithPaymentPairing, self).__init__(context)
        c = self.context
        if c.get('detail'):
            self.main.add(h1(_('Detail of payment')))
            self.main.add(adifdetails.BankStatementDetail(c.detail, c.history))
        if c.get('form'):
            self.main.add(c.form)

class MessageDetail(DetailPage):
    def __init__(self, context=None):
        super(MessageDetail, self).__init__(context)
        c = self.context
        if c.get('result'):
            self.main.add(h1(_('Detail_of_%s' % self.get_object_name())))
            self.main.add(adifdetails.MessageDetail(c.result, c.history))
            if config.debug:
                self.main.add('MessageDETAIL:', pre(unicode(c.result).replace(u', ', u',\n')))

class EditPage(BaseSiteMenu):
    def __init__(self, context=None):
        super(EditPage, self).__init__(context)
        c = self.context
        if c.get('form'):
            self.main.add(c.form)
            lang_code = config.lang[:2]
            if lang_code == 'cs': # conversion between cs and cz identifier of lagnguage
                lang_code = 'cz'
            self.head.add(
                script(attr(type='text/javascript'),
                'scwLanguage = "%s"; //sets language of js_calendar' % \
                lang_code,
                """scwDateOutputFormat = "%s"; // set output format for """
                """js_calendar""" % config.js_calendar_date_format_edit))


class RegistrarEdit(EditPage):
    pass


class BankStatementPairingEdit(EditPage):
    pass


class GroupEditorPage(BaseSiteMenu):
    def __init__(self, context=None):
        super(GroupEditorPage, self).__init__(context)
        c = self.context
        if c.get('form'):
            self.main.add(c.form)
            lang_code = config.lang[:2]
            if lang_code == 'cs': # conversion between cs and cz identifier of lagnguage
                lang_code = 'cz'
            self.head.add(
                script(attr(type='text/javascript'),
                'scwLanguage = "%s"; //sets language of js_calendar' % \
                lang_code,
                """scwDateOutputFormat = "%s"; // set output format for """
                """js_calendar""" % config.js_calendar_date_format_edit))


class DigPage(BaseSiteMenu):
    def __init__(self, context=None):
        super(DigPage, self).__init__(context)
        c = self.context
        self.main.add(h2(_('dig_query')))
        if c.get('handle'):
            self.main.add(h3(_('Domain'), c.handle))
        if c.get('dig'):
            self.main.add(pre(c.dig))


class SetInZoneStatusPage(BaseSiteMenu):
    def __init__(self, context=None):
        super(SetInZoneStatusPage, self).__init__(context)
        c = self.context
        self.main.add(h2(_('Set InZone Status')))
        if c.get('handle'):
            self.main.add(h3(_('Domain'), c.handle))
        if c.get('success') and c.success:
            self.main.add(pre(attr(style='color:green;'),
                              _("Function returns True.")))
        if c.get('error'):
            self.main.add(pre(attr(style='color:red;'), c.error))


class DomainBlocking(BaseSiteMenu):
    def __init__(self, context):
        super(DomainBlocking, self).__init__(context)
        c = self.context
        self.main.add(h1(c['heading']))
        if c.get('form'):
            self.main.add(c['form'])

        lang_code = config.lang[:2]
        if lang_code == 'cs':  # conversion between cs and cz identifier of lagnguage
            lang_code = 'cz'
        self.head.add(script(attr(type='text/javascript'),
                             'scwLanguage = "%s"; //sets language of js_calendar' % lang_code,
                             'scwDateOutputFormat = "%s"; // set output format for js_calendar' % config.js_calendar_date_format))


class DomainBlockingResult(BaseSiteMenu):
    def __init__(self, context):
        super(DomainBlockingResult, self).__init__(context)
        c = self.context
        self.main.add(h1(c['heading']))
        if c.get('blocked_objects'):
            self.main.add(
                p(_('These domains were successfully changed:')),
                ul(save(self, 'blocked_object_ul'))
            )

            for blocked_object in c['blocked_objects']:
                if c.get('holder_changes') and c.holder_changes.get(blocked_object.id):
                    old_holder = c.holder_changes[blocked_object.id]['old_holder']
                    new_holder = c.holder_changes[blocked_object.id]['new_holder']
                    holder_change_text = notag(', holder changed ', a(attr(href=old_holder['link']), old_holder['handle']),
                                               ' -> ', a(attr(href=new_holder['link']), new_holder['handle']))
                else:
                    holder_change_text = None
                self.blocked_object_ul.add(li(a(attr(href=c['detail_url'] % blocked_object.id), blocked_object.handle), holder_change_text))
