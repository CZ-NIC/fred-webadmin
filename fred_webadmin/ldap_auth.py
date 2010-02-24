import ldap
from fred_webadmin.controller.adif import AuthenticationError
from fred_webadmin import config
from fred_webadmin.translation import _

def authenticate_user(admin, username=None, password=None):
    """ Authenticate user using LDAP server.
    """
    try:
        l = ldap.open(config.LDAP_server)
        l.simple_bind_s(config.LDAP_scope % (username, password))
    except ldap.SERVER_DOWN:
        raise AuthenticationError(_('LDAP server is unavailable!'))
    except ldap.INVALID_CREDENTIALS:
        raise AuthenticationError(_('Invalid username and/or password!'))
