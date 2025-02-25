from logging import getLogger

import transaction
from plone import api

LOGGER = getLogger(__name__)


def upgrade(_):
    catalog = api.portal.get_tool("portal_catalog")
    brains = catalog(portal_type="Observation",
                     path={"query": "/Plone/2025", "depth": 1})

    brains_len = len(brains)
    a_tenth = brains_len / 10

    LOGGER.info("Found %s brains...", brains_len)

    observations = (b.getObject() for b in brains)

    acl_users = api.portal.get_tool("acl_users")

    for idx, observation in enumerate(observations, start=1):
        owner_info = observation.owner_info()
        if owner_info and owner_info["explicit"] and "acl_users" not in \
            owner_info["path"]:
            observation.changeOwnership(
                acl_users.getUserById(owner_info["id"]))

        # log progress
        if a_tenth and idx % a_tenth == 0:
            transaction.savepoint(optimistic=True)
            LOGGER.info("Done %s/%s.", idx, brains_len)
