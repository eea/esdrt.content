from Acquisition import aq_parent
from esdrt.content.question import IQuestion
from five import grok
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from .utils import notify


def notification_ms(context, event):
    """
    To:     MSAuthority
    When:   Answer Acknowledged
    """
    _temp = PageTemplateFile('answer_acknowledged.pt')

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
