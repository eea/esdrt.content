from Acquisition import aq_parent
from esdrt.content.question import IQuestion
from five import grok
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from .utils import notify


def notification_qe(context, event):
    """
    To:     QualityExpert
    When:   New question for approval
    """
    _temp = PageTemplateFile('question_ready_for_approval.pt')

    if event.action in ['phase1-send-to-lr']:
        observation = aq_parent(context)
        subject = 'New question for approval'
        notify(
            observation,
            _temp,
            subject,
            'QualityExpert',
            'question_ready_for_approval'
        )


def notification_lr(context, event):
    """
    To:     LeadReviewer
    When:   New question for approval
    """
    _temp = PageTemplateFile('question_ready_for_approval.pt')

    if event.action in ['phase2-send-to-lr']:
        observation = aq_parent(context)
        subject = 'New question for approval'
        notify(
            observation,
            _temp,
            subject,
            'LeadReviewer',
            'question_ready_for_approval'
        )
