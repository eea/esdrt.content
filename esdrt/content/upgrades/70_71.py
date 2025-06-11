from logging import getLogger

from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

from DateTime import DateTime

from Products.CMFCore.utils import getToolByName
import plone.api as api


def upgrade(context, logger=None):
    if logger is None:
        logger = getLogger("esdrt.content.upgrades.70_71")

    catalog = api.portal.get_tool("portal_catalog")

    query = {
        "portal_type": "Observation",
        "modified": {"query": DateTime() - 365, "range": "min"},
    }

    brains = catalog(**query)
    brains_len = len(brains)
    logger.info("Found %s brains.", brains_len)
    observations = (brain.getObject() for brain in brains)
    for idx, observation in enumerate(observations, start=1):
        logger.info("[%s/%s] Reindexing %s", idx, brains_len, observation.absolute_url())
        catalog.catalog_object(
            observation,
            idxs=("parameter", "qa_extract", "phase_timestamp"),
            update_metadata=1,
        )
        if idx % 50 == 0:
            logger.info("Done %s/%s.", idx, brains_len)
