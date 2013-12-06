class AdifError(Exception):
    def __init__(self, msg):
        self.msg = msg.encode("utf-8")

    def __str__(self):
        return self.msg


class PermissionDeniedError(AdifError):
    pass


class IorNotFoundError(AdifError):
    pass


class AuthenticationError(AdifError):
    pass


class AuthorizationError(AdifError):
    pass


class MalformedAuthorizationError(AuthorizationError):
    pass
