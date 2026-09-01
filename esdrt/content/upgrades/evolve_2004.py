from logging import getLogger

import plone.api as api

from esdrt.content.crf_code_matching import crf_codes_from_registry


def upgrade(_, logger=None):
    if logger is None:
        logger = getLogger("esdrt.content.upgrades.2004")

    catalog = api.portal.get_tool("portal_catalog")

    query = {
        "portal_type": ["ReviewFolder"],
    }

    brains = catalog(**query)

    for brain in brains:
        folder = brain.getObject()
        if folder.crf_code_mapping is None:
            logger.info("Setting crf_code_mapping for %s", folder.absolute_url(1))
            folder.crf_code_mapping = list(crf_codes_from_registry().values())

