from zope.component import getUtility
from zope.component.hooks import getSite

from esdrt.content.utilities.interfaces import ISetupReviewFolderRoles


def upgrade(_):
    portal = getSite()
    getUtility(ISetupReviewFolderRoles)(portal['2018'])