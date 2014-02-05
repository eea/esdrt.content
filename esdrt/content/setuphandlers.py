from Products.CMFCore.utils import getToolByName

import csv


VOCABULARIES = [
    {'id': 'eu_member_states',
     'title': 'EU Member States',
     'filename': 'eu_member_states.csv',
    },
    {'id': 'ghg_source_category',
     'title': 'GHG Source Category',
     'filename': 'ghg_source_category.csv',
    },
    {'id': 'ghg_source_sectors',
     'title': 'GHG Source Sectors',
     'filename': 'ghg_source_sectors.csv',
    },
    {'id': 'crf_code',
     'title': 'CRF Code',
     'filename': 'crf_code.csv',
    },
    {'id': 'status_flag',
     'title': 'Status Flag',
     'filename': 'status_flag.csv',
    },
]


def create_vocabulary(context, vocabname, vocabtitle, importfilename=None,
    profile=None):
    _ = context.invokeFactory(id=vocabname,
            title=vocabtitle,
            type_name='SimpleVocabulary',

        )
    vocabulary = context.getVocabularyByName(vocabname)
    # wtool = getToolByName(context, 'portal_workflow')
    # import pdb; pdb.set_trace()
    # wtool.doActionFor(vocabulary, 'publish')
    from logging import getLogger
    log = getLogger('create_vocabulary')
    log.info('Created %s vocabulary' % vocabname)
    if importfilename is not None:
        data = profile.readDataFile(importfilename, subdir='esdrtvocabularies')
        vocabulary.importCSV(data)
        # csvreader = csv.DictReader(data)
        # for item in csvreader:
        #     vocabulary.addTerm(key=item['term-id'], value=item['term-value'])
        #     log.info('Added term: %s - %s' %
        #         (item['term-id'], item['term-value']))

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


def setupVarious(context):
    """ various import steps for esdrt.content """
    portal = context.getSite()

    if context.readDataFile('esdrt.content_various.txt') is None:
        return

    prepareVocabularies(portal, context)