import sys
import types

import config
import fred_webadmin.corbarecoder as recoder

if config.permissions['enable_checking']:
    if config.permissions['backend'] == 'nicauth':
        import fred_webadmin.perms.nicauth as auth_user
    elif config.permissions['backend'] == 'csv':
        import fred_webadmin.perms.csvauth as auth_user
    else:
        raise Exception("No valid authorization module has been configured.")
else:
    import fred_webadmin.perms.dummy as auth_user

from fred_webadmin.webwidgets.utils import isiterable

class User(object):
    def __init__(self, user):
        ''' Wrapper around corba User object '''
        self._user = user # corba User object
        self.id = user._get_id()
        self.login = recoder.c2u(user._get_username())
        self.firstname = recoder.c2u(user._get_firstname())
        self.surname = recoder.c2u(user._get_surname())
        self.table_page_size = config.table_page_size

        self._authorizer = auth_user.Authorizer(self.login)

    def has_nperm(self, nperm, obj_id=None):
        ''' Return True, if nperm in self.nperms or any of its shorter versions created
            from it by stripping right part of it from "." character to end
            Example:
             if nperm is 'read.domain.authinfo' function returns True if one of following strings are in self.nperms:
                 'read', 'read.domain', 'read.domain.authinfo'
        '''
        parts = nperm.split('.')
        if obj_id is not None:
            # Is there any detailed permission starting with 'obj.action'?
            any_similar_detailed_perm_present = \
                self._authorizer.check_detailed_present(
                    parts[1], parts[0])
            if any_similar_detailed_perm_present:
                # Detailed permission detected => ignore high-level permission.
                has_perm = self._authorizer.has_permission_detailed(
                    parts[1], "%s.%s" % (parts[0], parts[2]), obj_id)
            else:
                # Detailed permission not present => check for high-level
                # permission.
                has_perm = self._authorizer.has_permission(parts[1], parts[0])
        else:
            # We're only checking for high-level permission.
            has_perm = self._authorizer.has_permission(parts[1], parts[0])
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

    def check_nperms(self, nperms, check_type='all'):
        'Returns True if user has NOT permission (has negative permission)'
        result = ((isinstance(nperms, types.StringTypes) and self.has_nperm(nperms)) or
                  (isiterable(nperms) and
                   (check_type == 'all' and self.has_all_nperms(nperms) or
                    check_type == 'one' and self.has_one_nperm(nperms))))
        return result
