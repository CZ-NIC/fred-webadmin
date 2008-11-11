#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import types
from translation import _
from mappings import f_urls

class MenuNode(object):
    _menudict = {}
    def __init__(self, handle, caption, body_id=None, cssc=None, url=None, submenu=None, nperm=None, nperm_type='all', default=False):
        ''' nperm defines negative permssion(s) - can be string or list of strings
            nperm type: if nperm is list, then nperm_type determinates whether to hide permission it is needed 'all' of them, or just 'one' of them (default is 'all')
            nperms of submenus are appended to self.nperm

            default: mean that this menu is default submenu, it means that if parent url is None, this default submenu's url will be taken for parent url
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
        
        self.default = default
        
        self.nperm = []
        if isinstance(nperm, types.StringTypes):
            self.nperm.append(nperm)
        elif nperm:
            self.nperm = nperm
        self.nperm_type = nperm_type
        
        self.submenus = []
        if submenu:
            submenu_default_present = False
            for smenu in submenu:
                self.submenus.append(smenu)
                smenu.parent = self
                self.nperm.extend(smenu.nperm)
                if smenu.default:
                    if submenu_default_present != True:
                        submenu_default_present = True
                    else:
                        raise RuntimeError('Menu specification error: there could be only one default submenu of menu!')
        
        self.nperm = list(set(self.nperm)) # only distinct values 
                
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
        return self._url
    def _set_url(self, value):
        self._url = value
    url = property(_get_url, _set_url)
    
    def mprint(self, level=0):
        output = ('\t' * level) + '%s (%s, %s, %s) %s' % (self.caption, self.cssc, self.body_id, self.url, ['', '*'][self.default]) + '\n'
        #output += ', '.join(self.nperm) + '\n'
        for smenu in self.submenus:
            output += smenu.mprint(level + 1)
        return output
    
    
    
menu_tree = MenuNode('root', '', '', 'menu-item', '#', [
    MenuNode('summary', _('Summary'), 'body-summary', 'menu-item menu-summary', url='/summary/'), 
    MenuNode('object', _('Objects'), 'body-objects', 'menu-item menu-objects', submenu=[
        MenuNode('domain', _('Search domains'), cssc='menu-item', url=f_urls['domain'] + 'allfilters/', nperm='read.domain'),
        MenuNode('contact', _('Search contacts'), cssc='menu-item', url=f_urls['contact'] + 'allfilters/', nperm='read.contact'),
        MenuNode('nsset', _('Search nssets'), cssc='menu-item', url=f_urls['nsset'] + 'allfilters/', nperm='read.nsset'),
        MenuNode('keyset', _('Search keysets'), cssc='menu-item', url=f_urls['keyset'] + 'allfilters/', nperm='read.keyset'),        
    ]), 
    MenuNode('registrar', _('Registrars'), 'body-registrars', 'menu-item menu-registrars', nperm='read.registrar', submenu=[
        MenuNode('registrarlist', _('List'), cssc='menu-item', url=f_urls['registrar'] + 'filter/?list_all=1', nperm='read.registrar'),
        MenuNode('registrarfilter', _('Search'), cssc='menu-item', url=f_urls['registrar'] + 'allfilters/', nperm='read.registrar', default=True),
        MenuNode('registrarcreate', _('Create new'), cssc='menu-item', url=f_urls['registrar'] + 'create/', nperm=['read.registrar', 'write.registrar'], nperm_type='one'),
        MenuNode('invoice', _('Invoices'), cssc='menu-item', url=f_urls['invoice'] + 'allfilters/', nperm='read.invoice'),
    ]), 
    MenuNode('logs', _('Logs'), 'body-logs', 'menu-item menu-logs', url='/logs/', submenu=[
        MenuNode('action', _('Actions'), cssc='menu-item', url=f_urls['action'] + 'allfilters/', nperm='read.action'),
        MenuNode('publicrequest', _('PublicRequests'), cssc='menu-item', url=f_urls['publicrequest'] + 'allfilters/', nperm='read.publicrequest'),
        MenuNode('mail', _('Emails'), cssc='menu-item', url=f_urls['mail'] + 'allfilters/', nperm='read.email'),
        MenuNode('zonegener', _('Zone gener.'), cssc='menu-item', url='/zonegener/', nperm='read.zonegener'),
        MenuNode('techtest', _('Tech. tests'), cssc='menu-item', url='/techtests/', nperm='read.techtest'),
    ]), 
    MenuNode('statistics', _('Statistics'), 'body-statistics', 'menu-item menu-statistics', url='/statistics/')
])


if __name__ == '__main__':
    print menu_tree.mprint()