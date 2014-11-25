from Acquisition import aq_parent
from DateTime import DateTime
from esdrt.content.observation import IObservation
from esdrt.content.question import IQuestion
from esdrt.content.commentanswer import ICommentAnswer
from five import grok
from plone import api
from Products.CMFCore.interfaces import IActionSucceededEvent
from Products.CMFCore.utils import getToolByName


@grok.subscribe(IQuestion, IActionSucceededEvent)
def question_transition(question, event):
    if event.action in ['phase1-approve-question', 'phase2-approve-question']:
        wf = getToolByName(question, 'portal_workflow')
        comment_id = wf.getInfoFor(question,
            'comments', wf_id='esd-question-review-workflow')
        comment = question.get(comment_id, None)
        if comment is not None:
            comment.setEffectiveDate(DateTime())
            api.content.transition(obj=comment, transition='publish')

    if event.action in ['phase2-approve-question']:
        observation = aq_parent(question)
        if api.content.get_state(observation) == 'phase2-draft':
            api.content.transition(obj=observation, transition='phase2-open')

    if event.action in ['phase1-recall-question-lr', 'phase2-recall-question-lr']:
        wf = getToolByName(question, 'portal_workflow')
        comment_id = wf.getInfoFor(question,
            'comments', wf_id='esd-question-review-workflow')
        comment = question.get(comment_id, None)
        if comment is not None:
            api.content.transition(obj=comment, transition='retract')

    if event.action in ['phase1-answer-to-lr', 'phase2-answer-to-lr']:
        wf = getToolByName(question, 'portal_workflow')
        comment_id = wf.getInfoFor(question,
            'comments', wf_id='esd-question-review-workflow')
        comment = question.get(comment_id, None)
        if comment is not None:
            comment.setEffectiveDate(DateTime())
            api.content.transition(obj=comment, transition='publish')

    if event.action in ['phase1-recall-msa', 'phase2-recall-msa']:
        wf = getToolByName(question, 'portal_workflow')
        comment_id = wf.getInfoFor(question,
            'comments', wf_id='esd-question-review-workflow')
        comment = question.get(comment_id, None)
        if comment is not None:
            api.content.transition(obj=comment, transition='retract')

#    if api.content.get_state(obj=event.object) == 'phase1-closed':
#        parent = aq_parent(event.object)
#        with api.env.adopt_roles(roles=['Manager']):
#            if api.content.get_state(parent) != 'phase1-conclusions':
#                api.content.transition(obj=parent, transition='phase1-draft-conclusions')
#
#    if api.content.get_state(obj=event.object) == 'phase2-closed':
#        parent = aq_parent(event.object)
#        with api.env.adopt_roles(roles=['Manager']):
#            if api.content.get_state(parent) != 'phase2-conclusions':
#                api.content.transition(obj=parent, transition='phase2-draft-conclusions')


@grok.subscribe(IObservation, IActionSucceededEvent)
def observation_transition(observation, event):
    if event.action == 'phase1-reopen':
        with api.env.adopt_roles(roles=['Manager']):
            qs = [q for q in observation.values() if q.portal_type == 'Question']
            if qs:
                q = qs[0]
                api.content.transition(obj=q, transition='phase1-reopen')

    elif event.action == 'phase2-reopen-qa-chat':
        with api.env.adopt_roles(roles=['Manager']):
            qs = [q for q in observation.values() if q.portal_type == 'Question']
            if qs:
                q = qs[0]
                api.content.transition(obj=q, transition='phase2-reopen')

    elif event.action in ['phase1-request-comments']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in observation.values() if c.portal_type == 'Conclusion']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='request-comments')

    elif event.action in ['phase1-finish-comments']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in observation.values() if c.portal_type == 'Conclusion']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='redraft')

    elif event.action in ['phase1-request-close']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in observation.values() if c.portal_type == 'Conclusion']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='publish')

    elif event.action in ['phase1-deny-closure']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in observation.values() if c.portal_type == 'Conclusion']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='redraft')

    elif event.action in ['phase2-request-comments']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in observation.values() if c.portal_type == 'ConclusionsPhase2']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='request-comments')

    elif event.action in ['phase2-finish-comments']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in observation.values() if c.portal_type == 'ConclusionsPhase2']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='redraft')

    elif event.action in ['phase2-finish-observation']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in observation.values() if c.portal_type == 'ConclusionsPhase2']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='publish')

    elif event.action in ['phase2-deny-finishing-observation']:
        with api.env.adopt_roles(roles=['Manager']):
            conclusions = [c for c in observation.values() if c.portal_type == 'ConclusionsPhase2']
            if conclusions:
                conclusion = conclusions[0]
                api.content.transition(obj=conclusion,
                    transition='redraft')

    elif event.action == 'phase1-draft-conclusions':
        with api.env.adopt_roles(roles=['Manager']):
            questions = [c for c in observation.values() if c.portal_type == 'Question']
            if questions:
                question = questions[0]
                if api.content.get_state(question) != 'phase1-closed':
                    api.content.transition(obj=question,
                        transition='phase1-close')

    elif event.action == 'phase2-draft-conclusions':
        with api.env.adopt_roles(roles=['Manager']):
            questions = [c for c in observation.values() if c.portal_type == 'Question']
            if questions:
                question = questions[0]
                if api.content.get_state(question) != 'phase2-closed':
                    api.content.transition(obj=question,
                        transition='phase2-close')

    elif event.action == 'phase1-send-to-team-2':
        with api.env.adopt_roles(roles=['Manager']):
            questions = [c for c in observation.values() if c.portal_type == 'Question']
            if questions:
                question = questions[0]
                api.content.transition(obj=question,
                    transition='phase2-reopen'
                )


from zope.lifecycleevent.interfaces import IObjectRemovedEvent


@grok.subscribe(ICommentAnswer, IObjectRemovedEvent)
def delete_answer(answer, event):
    question = aq_parent(answer)
    if api.content.get_state(obj=question).startswith('phase1-'):
        api.content.transition(obj=question,
            transition='phase1-delete-answer'
        )
    elif api.content.get_state(obj=question).startswith('phase2-'):
        api.content.transition(obj=question,
            transition='phase2-delete-answer'
        )
