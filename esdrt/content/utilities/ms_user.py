from zope.interface import Interface
from zope.interface import implementer

import plone.api as api


class IUserIsMS(Interface):
    """ Returns True if the user has
        the MSAuthority or MSExpert roles.
    """


@implementer(IUserIsMS)
class UserIsMS(object):
    def __call__(self, context, user=None):
        user = user or api.user.get_current()
        roles = api.user.get_roles(user=user, obj=context)
        return 'MSAuthority' in roles or 'MSExpert' in roles
