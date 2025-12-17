from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from .utils import notify


def notification_qe(context, event):
    """
    To:     QualityExpert
    When:   Observation finalisation request
    """
    _temp = ViewPageTemplateFile('observation_finalisation_request.pt')

    if event.action in ['phase1-request-close']:
        observation = context
        subject = 'Observation finalisation request'
        notify(
            observation,
            _temp,
            subject,
            'QualityExpert',
            'observation_finalisation_request'
        )


def notification_lr(context, event):
    """
    To:     LeadReviewer
    When:   Observation finalisation request
    """
    _temp = ViewPageTemplateFile('observation_finalisation_request.pt')

    if event.action in ['phase2-finish-observation']:
        observation = context
        subject = 'Observation finalisation request'
        notify(
            observation,
            _temp,
            subject,
            'LeadReviewer',
            'observation_finalisation_request'
        )
