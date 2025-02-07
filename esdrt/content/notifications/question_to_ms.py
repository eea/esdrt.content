import plone.api as api
from Acquisition import aq_parent
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from five import grok

from esdrt.content.question import IQuestion
from utils import notify


def make_sure_observation_is_pending(observation):
    """
    Replace carried-over state with pending, so that MS can view the new question.
    """
    if api.content.get_state(obj=observation) in ["phase1-carried-over",
                                                  "phase2-carried-over"]:
        wft = api.portal.get_tool("portal_workflow")
        wf = wft.getWorkflowById(wft.getChainFor("Observation")[0])
        wf_id = wf.getId()
        wh = observation.workflow_history
        current_state = wh[wf_id][-1]["review_state"]
        if current_state == "phase1-carried-over":
            wh[wf_id][-1]["review_state"] = "phase1-pending"
        elif current_state == "phase2-carried-over":
            wh[wf_id][-1]["review_state"] = "phase2-pending"

        # Very important! We are updating a dict inside a tuple inside a
        # PersistentMapping. The mapping needs to be notified of this.
        wh._p_changed = 1

        wf.updateRoleMappingsFor(observation)
        observation.reindexObjectSecurity()


@grok.subscribe(IQuestion, IActionSucceededEvent)
def notification_ms(context, event):
    """
    To:     MSAuthority
    When:   New question for your country
    """
    _temp = PageTemplateFile('question_to_ms.pt')

    if event.action in ['phase1-approve-question', 'phase2-approve-question']:
        observation = aq_parent(context)
        make_sure_observation_is_pending(observation)
        subject = u'New question for your country'
        notify(
            observation,
            _temp,
            subject,
            role='MSAuthority',
            notification_name='question_to_ms'
        )


@grok.subscribe(IQuestion, IActionSucceededEvent)
def notification_rev_ph1(context, event):
    """
    To:     ReviewerPhase1
    When:   Your question was sent to MS
    """
    _temp = PageTemplateFile('question_to_ms_rev_msg.pt')

    if event.action in ['phase1-approve-question']:
        observation = aq_parent(context)
        subject = u'Your observation was sent to MS'
        notify(
            observation,
            _temp,
            subject,
            role='ReviewerPhase1',
            notification_name='question_to_ms'
        )


@grok.subscribe(IQuestion, IActionSucceededEvent)
def notification_rev_ph2(context, event):
    """
    To:     ReviewerPhase2
    When:   Your question was sent to MS
    """
    _temp = PageTemplateFile('question_to_ms_rev_msg.pt')

    if event.action in ['phase2-approve-question']:
        observation = aq_parent(context)
        subject = u'Your observation was sent to MS'
        notify(
            observation,
            _temp,
            subject,
            role='ReviewerPhase2',
            notification_name='question_to_ms'
        )
