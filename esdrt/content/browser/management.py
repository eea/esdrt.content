import logging
from collections import Counter
from copy import deepcopy

import transaction

from zope.interface import alsoProvides

from Products.Five.browser import BrowserView

import plone.api as api
from plone.protect.interfaces import IDisableCSRFProtection

from esdrt.content.browser.carryover import add_to_wh
from esdrt.content.browser.carryover import catalog_with_children

logger = logging.getLogger(__name__)


class ReindexContext(BrowserView):
    def __call__(self):
        catalog = api.portal.get_tool("portal_catalog")
        catalog_with_children(catalog, self.context)
        return self.request.RESPONSE.redirect(self.context.absolute_url())


class FixCarryover(BrowserView):
    def fiddle_wf(self, wf, obj, action, state):
        wh = obj.workflow_history
        wf_id = wf.getId()
        history = deepcopy(wh[wf_id])
        last_entry = history[-1]

        old_value = (last_entry["action"], last_entry["review_state"])

        last_entry["action"] = action
        last_entry["review_state"] = state
        wh[wf_id] = history
        wf.updateRoleMappingsFor(obj)

        new_value = (last_entry["action"], last_entry["review_state"])

        return old_value, new_value

    def get_candidates(self):
        observations = (
            o
            for o in self.context.values()
            if hasattr(o, "carryover_from")
            and "closed" not in api.content.get_state(o)
        )
        for obs in observations:
            conclusion = obs.get_conclusion()
            if conclusion and api.content.get_state(conclusion) == "published":
                yield obs

    def get_actor(self, obs, wf):
        wh = obs.workflow_history
        wf_id = wf.getId()
        for entry in reversed(wh[wf_id]):
            if entry["review_state"] == "phase1-carried-over":
                return entry["actor"]

        return api.user.get_current().getId()

    def __call__(self):
        if self.context.getId() != "2026":
            return "Wrong year!"
        alsoProvides(self.request, IDisableCSRFProtection)

        candidates = list(self.get_candidates())
        count = Counter([o.carryover_from for o in candidates])
        state_count = Counter([api.content.get_state(o) for o in candidates])
        logger.info(count)
        logger.info(state_count)

        wft = api.portal.get_tool("portal_workflow")
        wf_obs = wft.getWorkflowById(wft.getChainFor("Observation")[0])
        wf_conclusion = wft.getWorkflowById(wft.getChainFor("Conclusion")[0])

        catalog = api.portal.get_tool("portal_catalog")

        for idx, obs in enumerate(candidates, start=1):
            logger.info("Updating %s...", obs.absolute_url(1))
            conclusion = obs.get_conclusion()
            actor = self.get_actor(obs, wf_obs)
            add_to_wh(wf_conclusion, conclusion, "redraft", "draft", actor)
            catalog_with_children(catalog, obs)

            if idx % 50 == 0:
                transaction.savepoint(optimistic=True)
                logger.info("Savepoint %s", idx)

        transaction.commit()
        logger.info("Done!")

        return (count, state_count)
