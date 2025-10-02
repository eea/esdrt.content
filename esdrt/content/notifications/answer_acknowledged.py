from Acquisition import aq_parent

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from .utils import notify


def notification_ms(context, event):
    """
    To:     MSAuthority
    When:   Answer Acknowledged
    """
    _temp = ViewPageTemplateFile('answer_acknowledged.pt')

    if event.action in ['phase1-validate-answer-msa', 'phase2-validate-answer-msa']:
        observation = aq_parent(context)
        subject = 'Your answer was acknowledged'
        notify(
            observation,
            _temp,
            subject,
            'MSAuthority',
            'answer_acknowledged'
        )
