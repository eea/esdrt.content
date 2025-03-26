from Acquisition import aq_parent
from esdrt.content.question import IQuestion
from five import grok
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from .utils import notify


@grok.subscribe(IQuestion, IActionSucceededEvent)
def notification_mse(context, event):
    """
    To:     MSExperts
    When:   New question for your country
    """
    _temp = PageTemplateFile('answer_to_msexperts.pt')

    if event.action in ['phase1-assign-answerer', 'phase2-assign-answerer']:
        observation = aq_parent(context)
        subject = 'New question for your country'
        notify(
            observation,
            _temp,
            subject,
            'MSExpert',
            'answer_to_msexperts'
        )
