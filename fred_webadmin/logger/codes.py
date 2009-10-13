
"""
    Error and warning codes for sessionlogger.
    The mandatory format of the logged request property is ("error", errorcode)
    or ("warning", warningcode).
"""

__all__ = ["codes"]


logcodes = {
    "AlreadyLoggedIn" : 0,
    "InvalidLogin" : 1,
    "AuthFailed" : 2,
}
