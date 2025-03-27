from esdrt.content.observation import IObservation
from five import grok
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from .utils import notify


def notification_lr(context, event):
    """
    To:     LeadReviewer
    When:   Observation handed over to phase 2
    """
    _temp = PageTemplateFile('observation_to_phase2.pt')

    if event.action in ['phase1-send-to-team-2']:
        observation = context
        subject = 'Observation handed over to phase 2'
        notify(
            observation,
            _temp,
            subject,
            'LeadReviewer',
            'observation_to_phase2'
        )


def notification_rev_ph2(context, event):
    """
    To:     ReviewerPhase2
    When:   Observation handed over to phase 2
    """
    _temp = PageTemplateFile('observation_to_phase2_rev_msg.pt')

    if event.action in ['phase1-send-to-team-2']:
        observation = context
        subject = 'Observation handed over to phase 2'
        notify(
            observation,
            _temp,
            subject,
            'ReviewerPhase2',
            'observation_to_phase2'
        )
