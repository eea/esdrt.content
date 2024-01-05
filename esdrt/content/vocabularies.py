import itertools
from plone import api

from zope.interface import implementer

from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary

import esdrt.content.constants as C
from esdrt.content.utils import request_context


def mk_term(key, value):
    return SimpleVocabulary.createTerm(key, key, value)


def permissions_to_dict(text):
    result = {}

    text = text.strip()

    if text:
        for entry in [x.strip() for x in text.split("\n")]:
            try:
                highlight_id, role_string = [x.strip() for x in entry.split(" ", 1)]
                result[highlight_id] = [x.strip() for x in role_string.split(",")]
            except ValueError:
                continue

    return result

@implementer(IVocabularyFactory)
class MSVocabulary(object):

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('eea_member_states')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class GHGSourceCategory(object):

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('ghg_source_category')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class GHGSourceSectors(object):

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('ghg_source_sectors')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class Gas(object):

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('gas')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class Fuel(object):

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('fuel')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

@implementer(IVocabularyFactory)
class Highlight(object):

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('highlight')

        # In some cases (such as a form group) the context can be a dict or
        # something else that's not a true Plone context.
        # Attempt to get the true context from the request.
        context = request_context(context)

        terms = []
        if voc is not None:
            from esdrt.content.reviewfolder import ReviewFolderMixin

            # [refs #159093]
            internal_flags = getattr(context, "internal_highlights", []) or []
            can_view_internal_flags = (
                ReviewFolderMixin.can_view_internal_flags()
            )

            # [refs #159094]
            excluded_highlights = getattr(
                context, "excluded_highlights", []) or []
            
            # [refs #261305 #261306]
            highlights_access_roles = permissions_to_dict(getattr(context, "highlights_access_roles", "") or "")
            user_roles = api.user.get_roles(obj=context)

            for key, value in voc.getVocabularyLines():
                # [refs #159093]
                if key in internal_flags and not can_view_internal_flags:
                    continue

                # [refs #159094]
                if key in excluded_highlights:
                    continue

                # [refs #261305 #261306]
                if highlights_access_roles.get(key) and not set(highlights_access_roles[key]).intersection(user_roles):
                    continue

                terms.append(SimpleVocabulary.createTerm(key, key, value))

        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class HighlightSelect(object):
    """ Clean version of the highlight vocabulary,
    used to filter the actual highlight vocabulary """

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('highlight')

        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                terms.append(SimpleVocabulary.createTerm(key, key, value))

        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class Parameter(object):

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('parameter')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class StatusFlag(object):

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('status_flag')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)


from .crf_code_matching import crf_codes

@implementer(IVocabularyFactory)
class CRFCode(object):

    def __call__(self, context):
        terms = []
        crfcodes = crf_codes()
        for key, value in crfcodes.items():
            # create a term - the arguments are the value, the token, and
            # the title (optional)
            terms.append(SimpleVocabulary.createTerm(key, key, value['title']))
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class Conclusions(object):

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('conclusion_reasons')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class ConclusionsPhase2(object):

    def __call__(self, context):
        pvoc = api.portal.get_tool('portal_vocabularies')
        voc = pvoc.getVocabularyByName('conclusion_phase2_reasons')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class Roles(object):

    def __call__(self, context):
        terms = list(itertools.starmap(
            mk_term, [
                ('Manager', 'Manager'),
                (C.ROLE_SE, 'Sector Expert'),
                (C.ROLE_RE, 'Review Expert'),
                (C.ROLE_QE, 'Quality Expert'),
                (C.ROLE_LR, 'Lead Reviewer'),
                (C.ROLE_RP1, 'Reviewer Phase 1'),
                (C.ROLE_RP2, 'Reviewer Phase 2'),
                (C.ROLE_MSA, 'MS Authority'),
                (C.ROLE_MSE, 'MS Expert'),
            ]))

        return SimpleVocabulary(terms)

