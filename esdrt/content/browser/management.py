import logging
from collections import Counter
from copy import deepcopy

import plone.api as api
import transaction
from plone.protect.interfaces import IDisableCSRFProtection
from Products.Five.browser import BrowserView
from zope.interface import alsoProvides

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

    def __call__(self):
        if self.context.getId() != "2026":
            return "Wrong year!"
        alsoProvides(self.request, IDisableCSRFProtection)

        candidates = [
            o
            for o in self.context.values()
            if hasattr(o, "carryover_from")
            and api.content.get_state(o) == "phase2-carried-over"
        ]
        count = Counter([o.carryover_from for o in candidates])
        state_count = Counter([api.content.get_state(o) for o in candidates])
        logger.info(count)
        logger.info(state_count)

        wft = api.portal.get_tool("portal_workflow")
        wf_obs = wft.getWorkflowById(wft.getChainFor("Observation")[0])
        wf_question = wft.getWorkflowById(wft.getChainFor("Question")[0])

        catalog = api.portal.get_tool("portal_catalog")

        action_obj = "phase1-reopen"
        action_question = "phase1-reopen"
        new_state_obj = "phase1-carried-over"
        new_state_question = "phase1-draft"

        for idx, obs in enumerate(candidates, start=1):
            logger.info("Updating %s...", obs.absolute_url(1))
            old_value, new_value = self.fiddle_wf(
                wf_obs, obs, action_obj, new_state_obj
            )
            logger.info("OLD: %s, NEW: %s", old_value, new_value)
            question = obs.get_question()
            if question:
                logger.info("Updating %s...", question.absolute_url(1))
                old_value, new_value = self.fiddle_wf(
                    wf_question,
                    question,
                    action_question,
                    new_state_question,
                )
                logger.info("OLD: %s, NEW: %s", old_value, new_value)
            catalog_with_children(catalog, obs)

            if idx % 50 == 0:
                transaction.savepoint(optimistic=True)
                logger.info("Savepoint %s", idx)

        transaction.commit()
        logger.info("Done!")

        return (count, state_count)
