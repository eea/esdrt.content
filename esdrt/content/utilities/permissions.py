from zope.security.interfaces import IPermission
from zope.component import queryUtility
from plone.autoform.interfaces import READ_PERMISSIONS_KEY
import plone.api as api


from zope.interface import Interface
from zope.interface import implementer

import plone.api as api


class ICheckFieldPermission(Interface):
    """ Check if the user can access the
        passed in context field.
    """


@implementer(ICheckFieldPermission)
class CheckFieldPermission(object):
    def __call__(self, context, interface, field, user=None):
        user = user or api.user.get_current()

        perms = interface.queryTaggedValue(READ_PERMISSIONS_KEY)
        perm_name = perms.get(field)

        if perm_name:
            perm = queryUtility(IPermission, name=perm_name)
            # XXX: context is not Aquisition wrapped, no inherited permissions.
            return api.user.has_permission(perm.title, user=user, obj=context)