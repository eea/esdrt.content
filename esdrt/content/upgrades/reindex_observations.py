from DateTime import DateTime

import plone.api as api


def reindex_observations(logger, indexes, days=365):
    if not isinstance(indexes, (list, tuple)):
        indexes = [indexes]

    catalog = api.portal.get_tool("portal_catalog")

    query = {
        "portal_type": "Observation",
        "modified": {"query": DateTime() - days, "range": "min"},
    }

    brains = catalog(**query)
    brains_len = len(brains)
    logger.info("Found %s brains.", brains_len)
    observations = (brain.getObject() for brain in brains)
    for idx, observation in enumerate(observations, start=1):
        logger.info(
            "[%s/%s] Reindexing %s", idx, brains_len, observation.absolute_url()
        )
        catalog.catalog_object(
            observation,
            idxs=indexes,
            update_metadata=1,
        )
        if idx % 50 == 0:
            logger.info("Done %s/%s.", idx, brains_len)
