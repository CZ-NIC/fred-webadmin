import ldap
import fred_webadmin.controller.adiferrors
from fred_webadmin import config
from fred_webadmin.translation import _


def authenticate_user(admin, username=None, password=None):  # pylint: disable=W0613
    """ Authenticate user using LDAP server.
    """
    try:
        l = ldap.open(config.LDAP_server)
        l.simple_bind_s(config.LDAP_scope % username, password)
    except ldap.SERVER_DOWN:
        raise fred_webadmin.controller.adiferrors.AuthenticationError(_('LDAP server is unavailable!'))
    except ldap.INVALID_CREDENTIALS:
        raise fred_webadmin.controller.adiferrors.AuthenticationError(_('Invalid username and/or password!'))
