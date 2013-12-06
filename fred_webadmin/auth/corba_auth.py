import fred_webadmin.corbarecoder as recoder
import fred_webadmin.controller.adiferrors
from fred_webadmin.corba import ccReg
from fred_webadmin.translation import _


def authenticate_user(admin, username=None, password=None):
    """ Authenticate user using CORBA backend.
    """
    try:
        admin.authenticateUser(recoder.u2c(username), recoder.u2c(password))
    except ccReg.Admin.AuthFailed:
        raise fred_webadmin.controller.adiferrors.AuthenticationError(
            _('Invalid username and/or password!'))
