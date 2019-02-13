import gc
from logging import getLogger

import transaction

from zope.globalrequest import getRequest

from Products.CMFCore.utils import getToolByName

import plone.api as api


logger = getLogger('esdrt.content.upgrades.56_57')


QUERIES = (
    dict(portal_type='ESDRTFile', review_state='initial'),
    dict(portal_type='Comment', review_state='initial'),
    dict(portal_type='Question', review_state='phase2-closed'),
)


WFS = dict(
    ESDRTFile='esd-file-workflow',
    Comment='esd-comment-workflow',
    Question='esd-question-review-workflow',
)


def get_observation(obj):
    if obj.portal_type == 'Observation':
        return obj

    if obj.portal_type == 'Plone Site':
        return

    return get_observation(obj.aq_parent)


def get_object(catalog, brain, url):
    try:
        return brain.getObject()
    except KeyError:
        logger.warn('Removing stale brain: %s', url)
        catalog.uncatalog_object(brain.getPath())


def reindex_or_catalog(catalog, content, url):
    try:
        content.reindexObjectSecurity()
    except KeyError:
        logger.warn('Cannot reindex. Calling catalog_object for %s!', url)
        catalog.catalog_object(content)


def upgrade(context):
    catalog = getToolByName(context, 'portal_catalog')
    wft = getToolByName(context, 'portal_workflow')
    reindex = []
    for query in QUERIES:
        ctwf = wft.getWorkflowById(WFS[query['portal_type']])
        brains = catalog(**query)

        brains_len = len(brains)
        for idx, brain in enumerate(brains, start=1):
            url = brain.getURL()
            content = get_object(catalog, brain, url)

            if content:
                ctwf.updateRoleMappingsFor(content)
                reindex.append(get_observation(content) or content)

                logger.info('Updated %s %s/%s.', url, idx, brains_len)

    reindex = set(reindex)
    logger.info('Reindexing %s objects...', len(reindex))
    for idx, obs in enumerate(reindex, start=1):
        reindex_or_catalog(catalog, content, url)
        if idx % 10 == 0:
            logger.info('transaction.commit after %s!', idx)
            transaction.commit()
            logger.info('gc.collect: %s!', gc.collect())


    logger.info('gc.collect: %s!', gc.collect())
