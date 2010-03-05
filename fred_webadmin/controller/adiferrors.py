class AdifError(Exception):
    pass


class PermissionDeniedError(AdifError):
    pass


class IorNotFoundError(AdifError):
    pass


class AuthenticationError(AdifError):
    pass
