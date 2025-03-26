import csv
import itertools
from plone import api

from zope.interface import implementer
from zope.component import getUtility

from plone.registry.interfaces import IRegistry

from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary

import esdrt.content.constants as c
from esdrt.content.utils import request_context

from .interfaces import IESDRTVocabularies

def mk_term(key, value):
    return SimpleVocabulary.createTerm(key, key, value)


def csv_entries(data: str):
    data = data.strip()
    if data:
        for key, value in csv.reader(data.split("\n")):
            yield key, value


def csv_to_terms(data: str):
    return [
        mk_term(key, value)
        for key, value in csv_entries(data)
    ]


def vocabulary_from_csv_string(data: str):
    return SimpleVocabulary(csv_to_terms(data))


def get_registry_interface_field_data(interface, field):
    registry = getUtility(IRegistry)
    registry_data = registry.forInterface(interface)

    return registry_data.__getattr__(field)


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
        csv_data = get_registry_interface_field_data(
            IESDRTVocabularies, "eea_member_states"
        )
        return vocabulary_from_csv_string(csv_data)


@implementer(IVocabularyFactory)
class GHGSourceCategory(object):

    def __call__(self, context):
        csv_data = get_registry_interface_field_data(
            IESDRTVocabularies, "ghg_source_category"
        )
        return vocabulary_from_csv_string(csv_data)


@implementer(IVocabularyFactory)
class GHGSourceSectors(object):

    def __call__(self, context):
        csv_data = get_registry_interface_field_data(
            IESDRTVocabularies, "ghg_source_sectors"
        )
        return vocabulary_from_csv_string(csv_data)


@implementer(IVocabularyFactory)
class Gas(object):

    def __call__(self, context):
        csv_data = get_registry_interface_field_data(
            IESDRTVocabularies, "gas"
        )
        return vocabulary_from_csv_string(csv_data)


@implementer(IVocabularyFactory)
class Fuel(object):

    def __call__(self, context):
        csv_data = get_registry_interface_field_data(
            IESDRTVocabularies, "fuel"
        )
        return vocabulary_from_csv_string(csv_data)

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
        csv_data = get_registry_interface_field_data(
            IESDRTVocabularies, "highlight"
        )
        return vocabulary_from_csv_string(csv_data)


@implementer(IVocabularyFactory)
class Parameter(object):

    def __call__(self, context):
        csv_data = get_registry_interface_field_data(
            IESDRTVocabularies, "parameter"
        )
        return vocabulary_from_csv_string(csv_data)


@implementer(IVocabularyFactory)
class StatusFlag(object):

    def __call__(self, context):
        csv_data = get_registry_interface_field_data(
            IESDRTVocabularies, "status_flag"
        )
        return vocabulary_from_csv_string(csv_data)


from esdrt.content.crf_code_matching import crf_codes

@implementer(IVocabularyFactory)
class CRFCode(object):

    def __call__(self, context):
        terms = []
        crfcodes = crf_codes()
        for key, value in list(crfcodes.items()):
            # create a term - the arguments are the value, the token, and
            # the title (optional)
            terms.append(SimpleVocabulary.createTerm(key, key, value['title']))
        return SimpleVocabulary(terms)


@implementer(IVocabularyFactory)
class Conclusions(object):

    def __call__(self, context):
        csv_data = get_registry_interface_field_data(
            IESDRTVocabularies, "conclusion_reasons"
        )
        return vocabulary_from_csv_string(csv_data)


@implementer(IVocabularyFactory)
class ConclusionsPhase2(object):

    def __call__(self, context):
        csv_data = get_registry_interface_field_data(
            IESDRTVocabularies, "conclusion_phase2_reasons"
        )
        return vocabulary_from_csv_string(csv_data)


@implementer(IVocabularyFactory)
class Roles(object):

    def __call__(self, context):
        terms = list(itertools.starmap(
            mk_term, [
                ('Manager', 'Manager'),
                (c.ROLE_SE, 'Sector Expert'),
                (c.ROLE_RE, 'Review Expert'),
                (c.ROLE_QE, 'Quality Expert'),
                (c.ROLE_LR, 'Lead Reviewer'),
                (c.ROLE_RP1, 'Reviewer Phase 1'),
                (c.ROLE_RP2, 'Reviewer Phase 2'),
                (c.ROLE_MSA, 'MS Authority'),
                (c.ROLE_MSE, 'MS Expert'),
            ]))

        return SimpleVocabulary(terms)

