#import apps.nicauth.models.user as auth_user commented out because this file is not used and only makes it hard to run nosetests with doctests
from fred_webadmin.controller.adiferrors import AuthorizationError
from fred_webadmin.translation import _

class Authorizer(object):
    """ Interface to the NIC auth module.
    """
    def __init__(self, username):
        try:
            self._auth_user = auth_user.User.objects.get(username=username)
            self.perms = self._auth_user.get_all_permissions()
        except auth_user.User.DoesNotExist:
            raise AuthorizationError(
                    _("Authorization record does not exist for user ") + \
                        str(username))

    def has_permission(self, obj, action):
        return self._auth_user.has_permission("daphne", obj, action)

    def has_permission_detailed(self, obj, action, obj_id):
        has_perm = (
            self._auth_user.has_permission("daphne", obj, action, obj_id))
        return has_perm

    def check_detailed_present(self, obj, action):
        """ Check whether there is any 4-parts permission starting with
            'obj.action'.
            model in icauth is e.g. "Domain"
            perm_action is e.g. "read.nic_auth"
        """
        for perm in self.perms:
            model = perm.permission_type.content_type.model
            perm_action = perm.permission_type.name.split(".")
            obj_id = perm.object_id
            if model == obj and perm_action[0] == action and obj_id is not None:
                return True
        return False
