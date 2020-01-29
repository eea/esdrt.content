from functools import partial
from itertools import takewhile
from logging import getLogger

from zope.component.hooks import getSite

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage

from Products.CMFCore.utils import getToolByName

import openpyxl
from DateTime import DateTime
from esdrt.content.roles.localrolesubscriber import grant_local_roles

LOG = getLogger("esdrt.content.carryover")


def _read_col(row, nr):
    val = row[nr].value
    return val.strip() if val else val


def _clear_local_roles(obj):
    obj.__ac_local_roles__ = None


def clear_and_grant_roles(obj):
    """ Clear any local roles already granted and grant just those
        that make sense in the current review folder context.

        [refs #105604] This makes sure that users that were granted
        local roles on the old observation will not continue to
        have them (e.g. CounterPart).
    """
    _clear_local_roles(obj)
    grant_local_roles(obj)


def _copy_obj(target, ob, new_id=None):
    orig_ob = ob
    ob_id = new_id or orig_ob.getId()
    ob = ob._getCopy(target)
    ob._setId(ob_id)
    target._setObject(ob_id, ob, suppress_events=True)
    return target[ob_id]


def _copy_and_flag(context, obj, new_id=None):
    _, _, year, index = (new_id or obj.getId()).split("-")
    ob = _copy_obj(context, obj, new_id=new_id)
    ob.carryover_from = year
    ob.review_year = int(year)

    LOG.info(
        "Copied %s -> %s", obj.absolute_url(1), ob.absolute_url(1),
    )

    return ob


def _obj_from_url(context, site_url, url):
    traversable = str(url.split(site_url)[-1][1:])
    return context.unrestrictedTraverse(traversable)


def replace_conclusion_text(workflows, obj, text):
    wft = workflows["tool"]
    in_phase2 = wft.getInfoFor(obj, "review_state").startswith("phase2")
    conclusion = (
        obj.get_conclusion_phase2() if in_phase2 else obj.get_conclusion()
    )
    if text and conclusion:
        conclusion.text = text


def prepend_qa(target, source):
    source_qa = source.get_question()
    target_qa = target.get_question()

    if source_qa and target_qa:
        for comment in source_qa.values():
            _copy_obj(target_qa, comment)

        ordering = target_qa.getOrdering()
        ordering.orderObjects(key="creation_date")

    elif source_qa and not target_qa:
        _copy_obj(target, source_qa)


def add_to_wh(wf, obj, action, state, actor):
    wh = obj.workflow_history
    wf_id = wf.getId()
    wh[wf_id] = wh[wf_id] + (
        {
            "comments": "Carryover force state",
            "actor": actor,
            "time": DateTime(),
            "action": action,
            "review_state": state,
        },
    )
    wf.updateRoleMappingsFor(obj)


def reopen_with_qa(workflows, obj, actor):
    wft = workflows["tool"]
    in_phase2 = wft.getInfoFor(obj, "review_state").startswith("phase2")
    if in_phase2:
        action_obj = "phase2-reopen-qa-chat"
        action_question = "phase2-reopen"
        new_state_obj = "phase2-pending"
        new_state_question = "phase2-draft"
    else:
        action_obj = "phase1-reopen"
        action_question = "phase1-reopen"
        new_state_obj = "phase1-pending"
        new_state_question = "phase1-draft"

    add_to_wh(workflows["observation"], obj, action_obj, "pending", actor)
    question = obj.get_question()
    if question:
        add_to_wh(
            workflows["question"],
            question,
            action_question,
            new_state_question,
            actor,
        )

    if in_phase2:
        wf_conclusion = workflows["conclusion2"]
        conclusion = obj.get_conclusion_phase2()
    else:
        wf_conclusion = workflows["conclusion"]
        conclusion = obj.get_conclusion()

    if conclusion:
        add_to_wh(wf_conclusion, conclusion, "redraft", "draft", actor)


def copy_direct(context, catalog, workflows, obj_from_url, row):
    source = _read_col(row, 0)
    conclusion_text = _read_col(row, 1)
    actor = _read_col(row, 2)

    obj = obj_from_url(source)
    ob = _copy_and_flag(context, obj)

    replace_conclusion_text(workflows, ob, conclusion_text)
    clear_and_grant_roles(ob)
    reopen_with_qa(workflows, ob, actor)

    catalog.catalog_object(ob)


def copy_complex(context, catalog, workflows, obj_from_url, row):
    source = _read_col(row, 0)
    older_source = _read_col(row, 1)
    conclusion_text = _read_col(row, 2)
    actor = _read_col(row, 3)

    obj = obj_from_url(source)
    older_obj = obj_from_url(older_source)

    ob = _copy_and_flag(context, obj, older_obj.getId())

    replace_conclusion_text(workflows, ob, conclusion_text)
    prepend_qa(ob, older_obj)
    clear_and_grant_roles(ob)
    reopen_with_qa(workflows, ob, actor)

    catalog.catalog_object(ob)


class CarryOverView(BrowserView):

    index = ViewPageTemplateFile("templates/carryover.pt")

    def __call__(self):
        return self.index()

    def start(self, action, xls):
        portal = getSite()
        wb = openpyxl.load_workbook(xls, read_only=True, data_only=True)
        sheet = wb.worksheets[0]

        sheet_rows = sheet.rows
        next(sheet_rows)  # skip first row (header)
        # extract rows with values
        valid_rows = tuple(
            takewhile(lambda row: any(c.value for c in row), sheet_rows)
        )

        context = self.context
        site_url = portal.absolute_url()
        obj_from_url = partial(_obj_from_url, context, site_url)
        catalog = getToolByName(portal, "portal_catalog")
        wft = getToolByName(portal, "portal_workflow")

        wf_obs = wft.getWorkflowById(wft.getChainFor("Observation")[0])
        wf_question = wft.getWorkflowById(wft.getChainFor("Question")[0])
        wf_conclusion = wft.getWorkflowById(wft.getChainFor("Conclusion")[0])
        wf_conclusion2 = wft.getWorkflowById(
            wft.getChainFor("ConclusionsPhase2")[0]
        )

        actions = dict(direct=copy_direct, complex=copy_complex)
        workflows = dict(
            tool=wft,
            observation=wf_obs,
            question=wf_question,
            conclusion=wf_conclusion,
            conclusion2=wf_conclusion2,
        )
        copy_func = partial(
            actions[action], context, catalog, workflows, obj_from_url,
        )

        for row in valid_rows:
            copy_func(row)

        if len(valid_rows) > 0:
            (
                IStatusMessage(self.request).add(
                    "Carryover successfull!", type="info"
                )
            )
        else:
            (IStatusMessage(self.request).add("No data provided!", type="warn"))
        self.request.RESPONSE.redirect(context.absolute_url())
