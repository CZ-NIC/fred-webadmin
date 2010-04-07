class AdifError(Exception):
    pass


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
