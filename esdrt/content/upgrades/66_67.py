from logging import getLogger

import transaction
from DateTime import DateTime
from plone import api

PROFILE_ID = 'profile-esdrt.content:default'

LOGGER = getLogger('esdrt.content.upgrades.66_67')


def recursive_reindex(catalog, obj):
    catalog.reindexObject(obj)
    for child in obj.objectValues():
        recursive_reindex(catalog, child)

def upgrade(_):
    catalog = api.portal.get_tool("portal_catalog")
    brains = catalog(portal_type="Observation", review_state="pending",
                     modified={"range": "min", "query": DateTime("2024/09/17")})

    brains_len = len(brains)
    a_tenth = brains_len / 10

    LOGGER.info("Found %s brains...", brains_len)

    observations = (b.getObject() for b in brains)

    wft = api.portal.get_tool("portal_workflow")
    wf = wft.getWorkflowById(wft.getChainFor("Observation")[0])
    wf_id = wf.getId()

    for idx, observation in enumerate(observations, start=1):
        LOGGER.info(observation.absolute_url(1))
        wh = observation.workflow_history
        wh[wf_id][-1]["review_state"] = "phase1-pending"

        wf.updateRoleMappingsFor(observation)

        recursive_reindex(catalog, observation)

        # log progress
        if a_tenth and idx % a_tenth == 0:
            transaction.savepoint(optimistic=True)
            LOGGER.info("Done %s/%s.", idx, brains_len)
