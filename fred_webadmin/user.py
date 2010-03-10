import sys
import types

import config
if config.enable_perms_checking:
    import apps.nicauth.models.user as auth_user

from logging import debug

from fred_webadmin.webwidgets.utils import isiterable
from fred_webadmin.controller.adiferrors import AuthorizationError

class User(object):
    def __init__(self, user):
        ''' Wrapper around corba User object '''
        self._user = user # corba User object
        self.id = user._get_id()
        self.login = user._get_username()
        self.firstname = user._get_firstname()
        self.surname = user._get_surname()
        self.table_page_size = config.tablesize

        if config.enable_perms_checking:
            try:
                self._auth_user = auth_user.User.objects.get(username=self.login)
            except auth_user.User.DoesNotExist:
                raise AuthorizationError(
                    "Authorization record for user %s does not exist!" % self.login)
        else:
            self._auth_user = None
        
    def has_nperm(self, nperm):
        ''' Return True, if nperm in self.nperms or any of its shorter versions created
            from it by stripping right part of it from "." character to end
            Example: 
             if nperm is 'read.domain.authinfo' function returns True if one of following strings are in self.nperms:
                 'read', 'read.domain', 'read.domain.authinfo'
        '''
        if not config.enable_perms_checking:
            # No checking => user is permitted to do anything.
            return False
        parts = nperm.split('.')
        has_perm = self._auth_user.has_permission("daphne", parts[1], parts[0])
        return not has_perm

    
    def has_all_nperms(self, nperms):
        if not nperms: # nprems are empty
            return False
        for nperm in nperms:
            if not self.has_nperm(nperm): # nperm not in self.nperms:
                return False
        return True
    
    def has_one_nperm(self, nperms):
        for nperm in nperms:
            if self.has_nperm(nperm):
                return True
        return False

    def check_nperms(self, nperms, check_type = 'all'):
        'Returns True if user has NOT permission (has negative permission)'
        result = ((isinstance(nperms, types.StringTypes) and self.has_nperm(nperms)) or 
                  (isiterable(nperms) and 
                   (check_type == 'all' and self.has_all_nperms(nperms) or
                    check_type == 'one' and self.has_one_nperm(nperms))))
        return result 
