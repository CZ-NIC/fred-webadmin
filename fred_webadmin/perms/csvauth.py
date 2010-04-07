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
        "testuser2","read.bankstatement"

        Doctests:
            Mock the _get_reader call, so that we do not actually read 
            from a file.
            >>> Authorizer._get_reader = lambda x : ([["user", "a1.o1", \
"a2.o2"], ["user2", "a3.o3", "a4.o4"]])
            >>> a = Authorizer("user")
            >>> a.has_permission("o1", "a1")
            True
            >>> a.has_permission("o2", "a1")
            False
            >>> a.has_permission("o3", "a3")
            False
            >>> a = Authorizer("unknown user")
            Traceback (most recent call last):
            ...
            AuthorizationError: Authorization record does not exist for user \
unknown user
    """
    source = config.permissions['csv_file']

    def _get_reader(self):
        try:
            return csv.reader(open(Authorizer.source, "rb"))
        except IOError, e:
            raise AuthorizationError(e)

    def __init__(self, username):
        object.__init__(self)
        reader = self._get_reader()
        self.perms = None
        # Find the line with permissions for user with @username
        for row in reader:
            if row[0] == username:
                self.perms = row[1:]
        if not self.perms:
            raise AuthorizationError(
                    _("Authorization record does not exist for user ") +\
                        str(username))
        self._check_for_malformed_perms()

    def _check_for_malformed_perms(self):
        for perm in self.perms:
            if len(perm.split(".")) != 2:
                raise MalformedAuthorizationError(
                    _("Malformed authorization record in csv file!"))

    def has_permission(self, obj, action):
        for perm in self.perms:
            parts = perm.split(".")
            if parts[1] == obj and parts[0] == action:
                return True
        return False
