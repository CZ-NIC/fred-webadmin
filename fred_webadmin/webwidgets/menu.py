#!/usr/bin/python
# -*- coding: utf-8 -*-

import types
import sys
from gpyweb.gpyweb import WebWidget, attr, tagid, ul, li, a, div
from fred_webadmin.menunode import MenuNode
from utils import isiterable

class Menu(ul):
    def __init__(self, menutree, selected_menu_handle, user, *content, **kwd):
        '''nperms are negaive permissions of currently logged user'''
        super(Menu, self).__init__(*content, **kwd)
        self.tag = 'ul'
        self.menutree = menutree
        self.selected_menu_handle = selected_menu_handle
        self.user = user
        
        self.open_nodes = [] 
        self.set_open_nodes()
        self.create_menu_tree()
        
        
    def set_open_nodes(self):
        '''Set selected node and all its parent nodes to open=True'''
        node = MenuNode.get_menu_by_handle(self.selected_menu_handle)
        while node:
            self.open_nodes.append(node)
            node = node.parent
    
    def get_url(self, menu):
        if menu.url:
            return menu.url
        if menu.submenus:
            first_available_menu = None
            for smenu in menu.submenus:
                if not first_available_menu and not self.user.check_nperms(smenu.nperm, smenu.nperm_type):
                    first_available_menu = smenu
                if smenu.default and not self.user.check_nperms(smenu.nperm, smenu.nperm_type):
                    return self.get_url(smenu)
            # no default menu, take first available:
            if first_available_menu:
                return self.get_url(first_available_menu)
    
    def create_menu_tree(self):
        for menu in self.menutree.submenus:
            if self.user.check_nperms(menu.nperm, menu.nperm_type):
                continue # user has negative permission for this menu -> don't display it
                
                
            menu_open = menu in self.open_nodes
            cssc = menu.cssc
                
            submenu = None
            if menu_open:
                cssc += ' selected-menu'
                if menu.submenus:
                    submenu = Menu(menu, self.selected_menu_handle, self.user)
            
            url = self.get_url(menu)

            self.add(li(attr(cssc=cssc), a(attr(href=url), menu.caption), submenu))

class MenuHoriz(Menu):
    "Menu for horizonal use (e.g. no nested ul ul), instead it is sequence of ul"
    def __init__(self, menutree, selected_menu_handle, user, *content, **kwd):
        self.submenu = None
        super(MenuHoriz, self).__init__(menutree, selected_menu_handle, user, *content, **kwd)
        self.tag = 'div'
        
        
    def create_menu_tree(self):
        self.add(ul(tagid('_menu1')))
        for menu in self.menutree.submenus:
            if self.user.check_nperms(menu.nperm, menu.nperm_type):
                continue # user has negative permission for this menu -> don't display it

            menu_open = menu in self.open_nodes
            cssc = menu.cssc
                
            if menu_open:
                cssc += ' selected-menu'
                if menu.submenus:
                    self.submenu = MenuHoriz(menu, self.selected_menu_handle, self.user)
            
            url = self.get_url(menu)
            
            self._menu1.add(li(attr(cssc=cssc), a(attr(href=url), menu.caption)))
        self.add(div(attr(cssc='cleaner'), ''))
        if self.submenu:
            self.add(div(attr(cssc='submenu'), self.submenu, div(attr(cssc='cleaner'), '')))#, div(attr(cssc='cleaner'), 'wtf??')))
    
