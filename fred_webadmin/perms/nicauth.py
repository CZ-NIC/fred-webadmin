import apps.nicauth.models.user as auth_user
from fred_webadmin.controller.adiferrors import AuthorizationError

class Authorizer(object):
    """ Interface to the NIC auth module.
    """
    def __init__(self, username):
        try:
            self._auth_user = auth_user.User.objects.get(username=username)
        except auth_user.User.DoesNotExist:
            raise AuthorizationError(
                    "Authorization record for user %s does not exist!" \
                        % username)

    def has_permission(self, obj, action):
        return self._auth_user.has_permission("daphne", obj, action)
