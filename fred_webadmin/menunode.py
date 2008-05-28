#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

sys.path.insert(0, '')

from translation import _
from mappings import f_urls

class MenuNode(object):
    _menudict = {}
    def __init__(self, handle, caption, body_id=None, cssc=None, url=None, submenu=None, nperm=None, nperm_type='all'):
        ''' nperm defines negative permssion(s) - can be string or list of strings
            nperm type: if nperm is list, then nperm_type determinates whether to hide permission it is needed 'all' of them, or just 'one' of them (default is 'all')
        '''
        self.parent = None
        self.handle = handle
        self.caption = caption

        self._body_id = None
        self.body_id = body_id

        self._cssc = None
        self.cssc = cssc
        
        self._url = None
        self.url = url
        
        self.nperm = nperm
        self.nperm_type = nperm_type
        
        self.submenus = []
        if submenu:
            for smenu in submenu:
                self.submenus.append(smenu)
                smenu.parent = self
        MenuNode._menudict[handle] = self
        
    @classmethod
    def get_menu_by_handle(cls, handle):
        return MenuNode._menudict.get(handle)
                    
    
    def _get_body_id(self):
        if self._body_id is not None:
            return self._body_id
        else:
            if self.parent:
                return self.parent.body_id
            else:
                return None
    def _set_body_id(self, value):
        self._body_id = value
    body_id = property(_get_body_id, _set_body_id)
    
    def _get_cssc(self):
        if self._cssc is not None:
            return self._cssc
        else:
            if self.parent:
                return self.parent.cssc
            else:
                return None
    def _set_cssc(self, value):
        self._cssc = value
    cssc = property(_get_cssc, _set_cssc)
        
    
    def _get_url(self):
        if self._url is not None:
            return self._url
        else:
            if self.parent:
                return self.parent.url
            else:
                return None
            
    def _set_url(self, value):
        self._url = value
    url = property(_get_url, _set_url)
    
    def mprint(self, level=0):
        output = ('\t' * level) + '%s (%s, %s, %s)' % (self.caption, self.cssc, self.body_id, self.url) + '\n'
        for smenu in self.submenus:
            output += smenu.mprint(level + 1)
        return output
    
    
    
menu_tree = MenuNode('root', '', '', 'menu-item', '#', [
    MenuNode('summary', _('Summary'), 'body-summary', 'menu-item menu-summary', url='/summary/'), 
    MenuNode('objects', _('Objects'), 'body-objects', 'menu-item menu-objects', url=f_urls['domains'] + 'allfilters/', nperm=['domain.read', 'contact.read', 'nsset.read'], submenu=[
        MenuNode('domains', _('Search domains'), cssc='menu-item', url=f_urls['domains'] + 'allfilters/', nperm='domain.read'),
        MenuNode('contacts', _('Search contacts'), cssc='menu-item', url=f_urls['contacts'] + 'allfilters/', nperm='contact.read'),
        MenuNode('nssets', _('Search nssets'), cssc='menu-item', url=f_urls['nssets'] + 'allfilters/', nperm='nsset.read'),
    ]), 
    MenuNode('registrars', _('Registrars'), 'body-registrars', 'menu-item menu-registrars', url=f_urls['registrars'] + 'filter/?cf=1', nperm='registrar.read', submenu=[
        MenuNode('registrarslist', _('List'), cssc='menu-item', url=f_urls['registrars'] + 'filter/?list_all=1', nperm='registrar.read'),
        MenuNode('registrarsfilter', _('Search'), cssc='menu-item', url=f_urls['registrars'] + 'allfilters/', nperm='registrar.read'),
        MenuNode('registrarscreate', _('Create new'), cssc='menu-item', url=f_urls['registrars'] + 'create/', nperm='registrar.create'),
        MenuNode('invoices', _('Invoices'), cssc='menu-item', url=f_urls['invoices'] + 'allfilters/', nperm='invoice.read'),
    ]), 
    MenuNode('logs', _('Logs'), 'body-logs', 'menu-item menu-logs', url='/logs/', submenu=[
        MenuNode('actions', _('Actions'), cssc='menu-item', url=f_urls['actions'] + 'allfilters/', nperm='action.read'),
        MenuNode('publicrequests', _('PublicRequests'), cssc='menu-item', url=f_urls['publicrequests'] + 'allfilters/', nperm='publicrequest.read'),
        MenuNode('mails', _('Emails'), cssc='menu-item', url=f_urls['mails'] + 'allfilters/', nperm='email.read'),
        MenuNode('zonegener', _('Zone gener.'), cssc='menu-item', url='/zonegener/', nperm='zonegener.read'),
        MenuNode('techtests', _('Tech. tests'), cssc='menu-item', url='/techtests/', nperm='techtest.read'),
    ]), 
    MenuNode('statistics', _('Statistics'), 'body-statistics', 'menu-item menu-statistics', url='/statistics/')
])
