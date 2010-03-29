class Authorizer(object):
    """ Implements the authorizer interface and allows every action.
        To be used when permission checking is disabled.
    """
    def __init__(self, username):
        self._username = username

    def has_permission(self, obj, action):
        return True
