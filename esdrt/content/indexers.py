from esdrt.content.commentanswer import ICommentAnswer
from esdrt.content.comment import IComment
from conclusion import IConclusion
from conclusionsphase2 import IConclusionsPhase2
from .observation import IObservation
import plone.api as api
from plone.app.discussion.interfaces import IConversation
from plone.app.textfield.interfaces import IRichTextValue
from plone.indexer import indexer
from Products.CMFPlone.utils import safe_unicode
from types import FloatType
from types import IntType
from types import ListType
from types import StringType
from types import TupleType
from types import UnicodeType
from zope.schema import getFieldsInOrder


@indexer(IObservation)
def observation_country(context):
    return context.country


@indexer(IObservation)
def observation_crf_code(context):
    return context.crf_code


@indexer(IObservation)
def observation_ghg_source_category(context):
    return context.ghg_source_category_value()


@indexer(IObservation)
def observation_ghg_source_sectors(context):
    return context.ghg_source_sectors_value()


@indexer(IObservation)
def observation_status_flag(context):
    return context.status_flag


@indexer(IObservation)
def observation_year(context):
    return context.year


@indexer(IObservation)
def observation_review_year(context):
    return str(context.review_year)


@indexer(IObservation)
def last_question_reply_number(context):
    return context.last_question_reply_number()


@indexer(IObservation)
def last_answer_reply_number(context):
    return context.last_answer_reply_number()


@indexer(IObservation)
def conclusion1_reply_number(context):
    replynum = 0
    conclusions = context.values(['Conclusion'])
    if conclusions:
        conclusion = conclusions[0]
        disc = IConversation(conclusion)
        return disc.total_comments

    return replynum


@indexer(IObservation)
def conclusion2_reply_number(context):
    replynum = 0
    conclusions = context.values(['ConclusionsPhase2'])
    if conclusions:
        conclusion = conclusions[0]
        disc = IConversation(conclusion)
        return disc.total_comments

    return replynum


@indexer(IObservation)
def SearchableText(context):
    items = []
    items.extend(index_fields(getFieldsInOrder(IObservation), context))
    try:
        questions = context.getFolderContents({'portal_type': 'Question'},
            full_objects=True
        )
        items.extend(to_unicode(context.id))
    except:
        questions = []
    try:
        conclusions = context.getFolderContents({'portal_type': 'Conclusion'},
            full_objects=True
        )
    except:
        conclusions = []
    try:
        conclusionsphase2 = context.getFolderContents(
            {'portal_type': 'ConclusionsPhase2'},
            full_objects=True
        )
    except:
        conclusionsphase2 = []

    for question in questions:
        comments = question.getFolderContents({'portal_type': 'Comment'},
            full_objects=True
        )
        answers = question.getFolderContents({'portal_type': 'CommentAnswer'},
            full_objects=True
        )
        for comment in comments:
            items.extend(index_fields(getFieldsInOrder(IComment), comment))
        for answer in answers:
            items.extend(index_fields(
                getFieldsInOrder(ICommentAnswer), answer)
            )

    for conclusion in conclusions:
        items.extend(index_fields(getFieldsInOrder(IConclusion), conclusion))

    for conclusion in conclusionsphase2:
        items.extend(index_fields(
            getFieldsInOrder(IConclusionsPhase2), conclusion)
        )

    return u' '.join(items)


def index_fields(fields, context):
    items = []
    for name, field in fields:
        value = getattr(context, name)
        if getattr(field, 'vocabularyName', None):
            if type(value) in [ListType, TupleType]:
                vals = [context._vocabulary_value(field.vocabularyName, v) for v in value]
            else:
                vals = context._vocabulary_value(field.vocabularyName, value)
            items.extend(to_unicode(vals))

        if IRichTextValue.providedBy(value):
            html = value.output
            transforms = api.portal.get_tool('portal_transforms')
            if isinstance(html, unicode):
                html = html.encode('utf-8')
            value = transforms.convertTo('text/plain',
                html, mimetype='text/html'
            ).getData().strip()
        if value:
            items.extend(to_unicode(value))

    return items


def to_unicode(value):
    if type(value) in (StringType, UnicodeType):
        return [safe_unicode(value)]
    elif type(value) in [IntType, FloatType]:
        return [safe_unicode(str(value))]
    elif type(value) in [ListType, TupleType]:
        return [' '.join(to_unicode(v)) for v in value if v]
    return []


def question_status(context):
    questions = [c for c in context.values() if c.portal_type == "Question"]
    if context.get_status() != 'phase1-pending' and context.get_status() != 'phase2-pending':
        if context.get_status() in ['phase2-conclusions',]:
            if questions:
                question_state = api.content.get_state(questions[-1])
                if question_state != 'phase2-closed':
                    return question_state
        return context.get_status()
    else:
        if questions:
            question = questions[0]
            state = api.content.get_state(question)
            if state in ['phase1-closed', 'phase2-closed']:
                if state in ['phase1-closed']:
                    return 'phase1-answered'
                else:
                    return 'phase2-answered'
            else:
                return state
        else:
            if context.get_status().startswith('phase1'):
                return "observation-phase1-draft"
            else:
                return "observation-phase2-draft"


@indexer(IObservation)
def observation_question_status(context):
    return question_status(context)


@indexer(IObservation)
def observation_status(context):
    return context.observation_status()


@indexer(IObservation)
def observation_questions_workflow(context):
    return context.observation_questions_workflow()


@indexer(IObservation)
def observation_step(context):
    try:
        status = context.get_status()
        if status.startswith("phase1"):
            return "step1"
        elif status.startswith("phase2"):
            return "step2"
        else:
            return status
    except:
        return None


@indexer(IObservation)
def last_answer_has_replies(context):
    try:
        return context.last_answer_reply_number() > 0
    except:
        return False


@indexer(IObservation)
def observation_already_replied(context):
    try:
        return context.observation_already_replied()
    except:
        return False


@indexer(IObservation)
def reply_comments_by_mse(context):
    try:
        return context.reply_comments_by_mse()
    except:
        return False


@indexer(IObservation)
def observation_sent_to_msc(context):
    try:
        questions = context.get_values_cat(['Question'])
        if questions:
            question = questions[0]
            winfo = question.workflow_history
            for witem in winfo.get('esd-question-review-workflow', []):
                if witem.get('review_state', '').endswith('-pending'):
                    return True
        return False
    except:
        return False


@indexer(IObservation)
def observation_sent_to_mse(context):
    try:
        questions = context.get_values_cat(['Question'])
        if questions:
            question = questions[0]
            winfo = question.workflow_history
            for witem in winfo.get('esd-question-review-workflow', []):
                if witem.get('review_state', '').endswith('-expert-comments'):
                    return True
        return False
    except:
        return False


@indexer(IObservation)
def observation_finalisation_reason(context):
    try:
        status = context.get_status()
        if status == 'phase1-closed':
            conclusions = [c for c in context.values() if c.portal_type == "Conclusion"]
            return conclusions[0] and conclusions[0].closing_reason or ' '
        elif status == 'phase2-closed':
            conclusions = [c for c in context.values() if c.portal_type == "ConclusionsPhase2"]
            return conclusions[0] and conclusions[0].closing_reason or ' '
        else:
            return None
    except:
        return None


@indexer(IObservation)
def observation_finalisation_reason_step1(context):
    try:
        conclusions = [
            c for c in context.values()
            if c.portal_type == "Conclusion"
        ]
        return conclusions[0] and conclusions[0].closing_reason or ' '
    except:
        return None


@indexer(IObservation)
def observation_finalisation_reason_step2(context):
    try:
        conclusions = [
            c for c in context.values()
            if c.portal_type == "ConclusionsPhase2"
        ]
        return conclusions[0] and conclusions[0].closing_reason or ' '
    except:
        return None


@indexer(IObservation)
def observation_finalisation_text_step1(context):
    try:
        conclusions = [
            c for c in context.values()
            if c.portal_type == "Conclusion"
        ]
        return conclusions[0] and conclusions[0].text or ''
    except:
        return None


@indexer(IObservation)
def observation_finalisation_text_step2(context):
    try:
        conclusions = [
            c for c in context.values()
            if c.portal_type == "ConclusionsPhase2"
        ]
        return conclusions[0] and conclusions[0].text or ''
    except:
        return None
