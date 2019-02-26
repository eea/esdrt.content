import gc
from logging import getLogger

import transaction

from Products.CMFCore.utils import getToolByName

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

import plone.api as api

logger = getLogger('esdrt.content.upgrades.portal_workflow')


QUERIES = (
    dict(portal_type='ESDRTFile', review_state='initial'),
    dict(portal_type='Comment', review_state='initial'),
    dict(portal_type='Question', review_state='phase2-closed'),
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


def upgrade(wft, catalog, type_mapping, queries):
    reindex = []
    for _query in queries:
        # filter 'reindex_self_only', which is not an index
        query = {k: v for k, v in _query.items() if k != 'reindex_self_only'}
        ctwf = wft.getWorkflowById(type_mapping[query['portal_type']])
        brains = catalog(**query)

        brains_len = len(brains)
        for idx, brain in enumerate(brains, start=1):
            url = brain.getURL()
            content = get_object(catalog, brain, url)

            if content:
                ctwf.updateRoleMappingsFor(content)
                if _query.get('reindex_self_only', False):
                    reindex.append(content)
                else:
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


class ApplyAndReindex(BrowserView):
    """ Developer page to aid in applying workflow permission changes. """

    index = ViewPageTemplateFile('templates/portal_workflow_apply_and_reindex.pt')

    def __call__(self):
        request = self.request
        context = self.context

        catalog = getToolByName(context, 'portal_catalog')

        if request.method == 'POST':
            default_wf = context._default_chain[0]
            type_mapping = {
                k: v[0] if v else default_wf
                for k, v in context._chains_by_type.items()
            }
            queries =  request.get('queries', [])
            upgrade(context, catalog, type_mapping, queries)
            return 'Updated! Please refer to zinstance log for information.'

        # get information from catalog indexes
        indexes = catalog._catalog.indexes

        portal_types = sorted(set(indexes['portal_type']._unindex.itervalues()))
        review_states = sorted(set(indexes['review_state']._unindex.itervalues()))

        return self.index(portal_types=portal_types, review_states=review_states)
