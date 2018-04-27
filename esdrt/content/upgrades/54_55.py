import logging

from zope.component import getUtility
from zope.component.hooks import getSite

from esdrt.content.utilities.interfaces import ISetupReviewFolderRoles

logger = logging.getLogger('esdrt.content.upgrades.54_55')


def upgrade(_):
    portal = getSite()
    try:
        target = portal['2018']
        getUtility(ISetupReviewFolderRoles)(target)
    except KeyError:
        logger.warn('2018 folder missing! Nothing done.')