from esdrt.content.observation import IObservation
from five import grok
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from utils import notify


@grok.subscribe(IObservation, IActionSucceededEvent)
def notification_ms(context, event):
    """
    To:     MSAuthority
    When:   Observation was finalised
    """
    _temp = PageTemplateFile('observation_finalised.pt')
    _temp_remarks = PageTemplateFile('observation_finalised_ms_remarks.pt')

    _subj = u'An observation for your country was finalised'
    _subj_remarks = u'Observation finalised with a concluding remark'

    _act_ph1 = 'phase1-close'
    _act_ph2 = 'phase2-confirm-finishing-observation'

    if event.action in [_act_ph1, _act_ph2]:
        observation = context

        subject = _subj
        tpl = _temp

        tpl_remarks = False

        if event.action == _act_ph1:
            tpl_remarks = bool(observation.get_conclusion().remarks)

        elif event.action == _act_ph2:
            tpl_remarks = bool(observation.get_conclusion_phase2().remarks)

        if tpl_remarks:
            subject = _subj_remarks
            tpl = _temp_remarks

        notify(
            observation,
            tpl,
            subject,
            'MSAuthority',
            'observation_finalised'
        )


@grok.subscribe(IObservation, IActionSucceededEvent)
def notification_rev_ph1(context, event):
    """
    To:     ReviewerPhase1
    When:   Observation finalised
    """
    _temp = PageTemplateFile('observation_finalised_rev_msg.pt')
    if event.action in ['phase1-close']:
        observation = context
        subject = u'Your observation was finalised'
        notify(
            observation,
            _temp,
            subject,
            'ReviewerPhase1',
            'observation_finalised'
        )


@grok.subscribe(IObservation, IActionSucceededEvent)
def notification_rev_ph2(context, event):
    """
    To:     ReviewerPhase2
    When:   Observation finalised
    """
    _temp = PageTemplateFile('observation_finalised_rev_msg.pt')
    if event.action in ['phase2-confirm-finishing-observation']:
        observation = context
        subject = u'Your observation was finalised'
        notify(
            observation,
            _temp,
            subject,
            'ReviewerPhase2',
            'observation_finalised'
        )
