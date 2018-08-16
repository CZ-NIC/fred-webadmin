import csv
import fred_webadmin.config as config
from fred_webadmin.controller.adiferrors import (
    AuthorizationError, MalformedAuthorizationError)
from fred_webadmin.translation import _


class Authorizer(object):
    """
        Takes permissions from a csv file. The format of the data is:
        username1,perm1,perm2,perm3
        username2,perm1,perm2
        E.g.:
        "testuser","read.registrar","change.domain"
        "testuser2","read.invoice"

        Doctests:
            Mock the _get_reader call, so that we do not actually read
            from a file.
            >>> Authorizer._get_reader = lambda x : ([["user", "a1.o1", "a2.o2", "!a2.o2.c2", "!a3.o3.c3"], \
                                                      ["user2", "a3.o3", "a4.o4"]])
            >>> a = Authorizer("user")
            >>> a.has_permission("o1", "a1")
            True
            >>> a.has_permission("o2", "a1")
            False
            >>> a.has_permission("o2", "a2")
            True
            >>> a.has_field_permission("o2", "a2", "c2")
            False
            >>> a.has_field_permission("o2", "a2", "else")
            True
            >>> a.has_permission("o3", "a3")
            False
            >>> a.has_field_permission("o3", "a3", "c3")
            False
            >>> a.has_field_permission("o3", "a3", "else")
            False
            >>> a = Authorizer("unknown user")
            Traceback (most recent call last):
            ...
            AuthorizationError: Authorization record does not exist for user unknown user
    """
    source = config.permissions['csv_file']

    def _get_reader(self):
        try:
            return csv.reader(open(Authorizer.source, "rb"))
        except IOError, e:
            raise AuthorizationError(str(e))

    def __init__(self, username):
        object.__init__(self)
        reader = self._get_reader()
        self.perms = []
        self.field_nperms = []
        # Find the line with permissions for user with @username
        for row in reader:
            if not row:
                continue
            if row[0] == username:
                perm_records = row[1:]
                for perm in perm_records:
                    perm = perm.lower()
                    self._check_for_malformed_perm(perm)
                    parts = perm.split(".")
                    if len(parts) == 3:
                        perm = perm[1:]  # remove leading exclamation mark
                        self.field_nperms.append(perm)
                    else:
                        self.perms.append(perm)
        if not self.perms:
            raise AuthorizationError(_("Authorization record does not exist for user ") + username)

    def _check_for_malformed_perm(self, perm):
        perm_len = len(perm.split("."))
        if not 2 <= perm_len <= 4:
            raise MalformedAuthorizationError(
                _("Malformed authorization record in csv file: '%s'!" % perm))
        if perm_len == 3 and not perm.startswith('!'):
            raise MalformedAuthorizationError(
                _("Malformed authorization record in csv file: '%s'! Field negative permission must start with '!'" % perm))

    def check_detailed_present(self, obj, action):
        """ Check whether there is any 4-parts permission starting with
            'obj.action'.
        """
        return any([perm for perm in [item.split(".") for item in self.perms]
            if perm[1] == obj and perm[0] == action and
            len(perm) == 4])

    def has_field_permission(self, obj, action, field_name):
        if not self.has_permission(obj, action):
            return False
        return '%s.%s.%s' % (action, obj, field_name) not in self.field_nperms

    def has_permission(self, obj, action):
        for perm in self.perms:
            parts = perm.split(".")
            if parts[1] == obj and parts[0] == action:
                return True
        return False

    def has_permission_detailed(self, obj, action, obj_id):
        """ example arguments: domain, read.auth_info, 42
            example perm in file: read.domain.auth_info.42
        """
        for perm in self.perms:
            parts = perm.split(".")
            if len(parts) != 4:
                continue
            composed_part = "%s.%s" % (parts[0], parts[2])  # example: read.auth_info
            if (composed_part == action and parts[1] == obj and
                    parts[3] == str(obj_id)):
                return True
        return False
