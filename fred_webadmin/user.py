import sys
import types

from logging import debug

import config
from fred_webadmin.webwidgets.utils import isiterable

class User(object):
    def __init__(self, user):
        ''' Wrapper around corba User object '''
        self._user = user # corba User object
        self.id = user._get_id()
        self.login = user._get_username()
        self.firstname = user._get_firstname()
        self.surname = user._get_surname()
        self.table_page_size = config.tablesize
        
        # negative permissions or forbiddance 
#        self.nperms = ['domain.read', 'domain.create', 'domain.change', 'domain.delete',
#                       'contact.read', 'contact.create', 'contact.change', 'contact.delete',
#                       'nsset.read', 'nsset.create', 'nsset.change', 'nsset.delete',
#                       'registrar.read', 'registrar.create', 'registrar.change', 'registrar.delete',
#                      ]
        #self.nperms = ['domain.read', 'contact.read', 'nsset.read']
        #self.nperms = ['domain.read', 'domain.filter.owner', 'domain.filter.email']
        #self.nperms = ['registrar.read']
        if self.login == 'helpdesk':
            self.nperms = ['domain.filter', 'domain.filter.authinfo', 
                           'registrar.detail.city', 'registrar.change.street2', 'registrar.filter.city',
                           'domain.detail.createdate', 'domain.detail.authinfo']
            self.nperms = []
        else:
            self.nperms = ['domain.filter.admincontact']
        #self.nperms = []
        debug('Created user with nperms = %s' % str(self.nperms))
        
    def has_nperm(self, nperm):
        return nperm.lower() in self.nperms
        #return self._user.hasNPermission(nperm)
    
    def has_all_nperms(self, nperms):
        for nperm in nperms:
            if not self.has_nperm(nperm): # nperm not in self.nperms:
                return False
        return True
    
    def has_one_nperms(self, nperms):
        for nperm in nperms:
            if self.has_nperm(nperm):
                return True
            return False
#        if not nperms:
#            return True
#        else:
#            for nperm in nperms:
#                if nperm in self.nperms:
#                    return True
#            return False

    def check_nperms(self, nperms, check_type = 'all'):
        'Returns True if user has NOT permmission (has negative permission)'
        #debug('USER NPERM pri checku: %s, proti %s, check_type %s' % (self.nperms, nperms, check_type))  
        result = ((isinstance(nperms, types.StringTypes) and self.has_nperm(nperms)) or 
                  (isiterable(nperms) and 
                   (check_type == 'all' and self.has_all_nperms(nperms) or
                    check_type == 'one' and self.has_one_nperms(nperms))
                  )
                 )
        #print ' -> %s' % result
        return result 
