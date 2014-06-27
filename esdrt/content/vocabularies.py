from five import grok
from Products.CMFCore.utils import getToolByName
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary


class MSVocabulary(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = getToolByName(context, 'portal_vocabularies')
        voc = pvoc.getVocabularyByName('eea_member_states')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(MSVocabulary, name=u"esdrt.content.eea_member_states")


class GHGSourceCategory(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = getToolByName(context, 'portal_vocabularies')
        voc = pvoc.getVocabularyByName('ghg_source_category')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(GHGSourceCategory,
    name=u"esdrt.content.ghg_source_category")


class GHGSourceSectors(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = getToolByName(context, 'portal_vocabularies')
        voc = pvoc.getVocabularyByName('ghg_source_sectors')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(GHGSourceSectors,
    name=u"esdrt.content.ghg_source_sectors")


class Gas(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = getToolByName(context, 'portal_vocabularies')
        voc = pvoc.getVocabularyByName('gas')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(Gas,
    name=u"esdrt.content.gas")


class Fuel(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = getToolByName(context, 'portal_vocabularies')
        voc = pvoc.getVocabularyByName('fuel')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(Fuel,
    name=u"esdrt.content.fuel")


class Highlight(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = getToolByName(context, 'portal_vocabularies')
        voc = pvoc.getVocabularyByName('highlight')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(Highlight,
    name=u"esdrt.content.highlight")


class Parameter(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = getToolByName(context, 'portal_vocabularies')
        voc = pvoc.getVocabularyByName('parameter')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(Parameter,
    name=u"esdrt.content.parameter")


class StatusFlag(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = getToolByName(context, 'portal_vocabularies')
        voc = pvoc.getVocabularyByName('status_flag')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(StatusFlag,
    name=u"esdrt.content.status_flag")


class CRFCode(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        pvoc = getToolByName(context, 'portal_vocabularies')
        voc = pvoc.getVocabularyByName('crf_code')
        terms = []
        if voc is not None:
            for key, value in voc.getVocabularyLines():
                # create a term - the arguments are the value, the token, and
                # the title (optional)
                terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(CRFCode,
    name=u"esdrt.content.crf_code")


CLOSING_REASONS = [
    ('reason1', 'Reason 1'),
    ('reason2', 'Reason 2'),
    ('reason3', 'Reason 3'),
    ('reason4', 'Reason 4'),
]


class ClosingReasons(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        terms = []
        for key, value in CLOSING_REASONS:
            # create a term - the arguments are the value, the token, and
            # the title (optional)
            terms.append(SimpleVocabulary.createTerm(key, key, value))
        return SimpleVocabulary(terms)

grok.global_utility(ClosingReasons,
    name=u"esdrt.content.closingreasons")
