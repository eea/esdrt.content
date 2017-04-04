from logging import getLogger

from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

from Products.CMFCore.utils import getToolByName
import plone.api as api


def upgrade(context, logger=None):
    if logger is None:
        logger = getLogger('esdrt.content.upgrades.48_49')

    catalog = api.portal.get_tool('portal_catalog')

    brains = catalog(portal_type='Observation')
    brains_len = len(brains)
    logger.info('Found %s brains.', brains_len)
    observations = (brain.getObject() for brain in brains)
    for idx, observation in enumerate(observations, start=1):
        catalog.catalog_object(
            observation,
            idxs=('observation_status', ),
            update_metadata=1
        )
        if idx % 50 == 0:
            logger.info('Done %s/%s.', idx, brains_len)
