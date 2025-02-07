from logging import getLogger

import transaction
from plone import api

PROFILE_ID = 'profile-esdrt.content:default'

LOGGER = getLogger(__name__)


def recursive_reindex(catalog, obj):
    catalog.reindexObject(obj)
    catalog.reindexObjectSecurity(obj)
    for child in obj.objectValues():
        recursive_reindex(catalog, child)


def upgrade(_):
    catalog = api.portal.get_tool("portal_catalog")
    brains = catalog(portal_type="Observation",
                     review_state={
                         "query": ["phase1-pending", "phase2-pending"],
                         "operator": "or"},
                     path={"query": "/Plone/2025", "depth": 1})

    brains_len = len(brains)
    a_tenth = brains_len / 10

    LOGGER.info("Found %s brains...", brains_len)

    observations = (b.getObject() for b in brains)

    wft = api.portal.get_tool("portal_workflow")
    wf = wft.getWorkflowById(wft.getChainFor("Observation")[0])
    wf_id = wf.getId()

    for idx, observation in enumerate(observations, start=1):
        if str(observation.review_year) != "2025":
            LOGGER.info(observation.absolute_url(1))
            wh = observation.workflow_history
            current_state = wh[wf_id][-1]["review_state"]
            if current_state == "phase1-pending":
                wh[wf_id][-1]["review_state"] = "phase1-carried-over"
            elif current_state == "phase2-pending":
                wh[wf_id][-1]["review_state"] = "phase2-carried-over"

            wh._p_changed = 1

            wf.updateRoleMappingsFor(observation)

            recursive_reindex(catalog, observation)

            # log progress
            if a_tenth and idx % a_tenth == 0:
                transaction.savepoint(optimistic=True)
                LOGGER.info("Done %s/%s.", idx, brains_len)
