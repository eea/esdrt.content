from Products.CMFCore.utils import getToolByName
from Products.ATVocabularyManager.config import SORT_METHOD_FOLDER_ORDER


VOCABULARIES = [
    {'id': 'eea_member_states',
     'title': 'EEA Member States',
     'filename': 'eea_member_states.csv',
    },
    {'id': 'ghg_source_category',
     'title': 'CRF category group',
     'filename': 'ghg_source_category.csv',
    },
    {'id': 'ghg_source_sectors',
     'title': 'CRF Sector',
     'filename': 'ghg_source_sectors.csv',
    },
    {'id': 'fuel',
     'title': 'Fuel',
     'filename': 'fuel.csv',
    },
    {'id': 'gas',
     'title': 'Gas',
     'filename': 'gas.csv',
    },
    {'id': 'highlight',
     'title': 'Highligt',
     'filename': 'highlight.csv',
    },
    {'id': 'parameter',
     'title': 'Parameter',
     'filename': 'parameter.csv',
    },
    {'id': 'conclusion_reasons',
     'title': 'Conclusion Reasons',
     'filename': 'conclusion_reasons.csv',
    },
    {'id': 'conclusion_phase2_reasons',
     'title': 'Conclusion Phase2 Reasons',
     'filename': 'conclusion_phase2_reasons.csv',
    },
]


def create_vocabulary(context, vocabname, vocabtitle, importfilename=None,
    profile=None):
    _ = context.invokeFactory(id=vocabname,
            title=vocabtitle,
            type_name='SimpleVocabulary',

        )
    vocabulary = context.getVocabularyByName(vocabname)
    vocabulary.setSortMethod(SORT_METHOD_FOLDER_ORDER)
    wtool = getToolByName(context, 'portal_workflow')
    wtool.doActionFor(vocabulary, 'publish')
    from logging import getLogger
    log = getLogger('create_vocabulary')
    log.info('Created %s vocabulary' % vocabname)
    if importfilename is not None:
        data = profile.readDataFile(importfilename, subdir='esdrtvocabularies')
        vocabulary.importCSV(data)

    for term in vocabulary.values():
        wtool.doActionFor(term, 'publish')

    log.info('done')


def prepareVocabularies(context, profile):
    """ initial population of vocabularies """

    atvm = getToolByName(context, 'portal_vocabularies')

    for vocabulary in VOCABULARIES:
        vocab = atvm.getVocabularyByName(vocabulary.get('id'))
        if vocab is None:
            create_vocabulary(atvm,
                vocabulary.get('id'),
                vocabulary.get('title'),
                vocabulary.get('filename', None),
                profile
            )


def enable_atd_spellchecker(portal):
    tinymce = getToolByName(portal, 'portal_tinymce')
    tinymce.libraries_spellchecker_choice = u'AtD'
    tinymce.libraries_atd_service_url = u'service.afterthedeadline.com'


def setupVarious(context):
    """ various import steps for esdrt.content """
    portal = context.getSite()

    if context.readDataFile('esdrt.content_various.txt') is None:
        return

    prepareVocabularies(portal, context)
    enable_atd_spellchecker(portal)
