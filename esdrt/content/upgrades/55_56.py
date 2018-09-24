import gc
from logging import getLogger

import transaction

from zope.globalrequest import getRequest

from Products.CMFCore.utils import getToolByName

import plone.api as api


logger = getLogger('esdrt.content.upgrades.55_56')


PROFILE_ID = 'profile-esdrt.content:default'


WORKFLOWS = (
    'esd-answer-workflow',
    'esd-comment-workflow',
    'esd-conclusion-phase2-workflow',
    'esd-conclusion-workflow',
    'esd-file-workflow',
    'esd-question-review-workflow',
    'esd-review-workflow',
    'esd-reviewtool-folder-workflow',
)


PERMISSIONS = (
    'Access contents information',
    'View',
)

TYPES = (
    'ConclusionsPhase2',
    'Conclusion',
    'ESDRTFile',
    'CommentAnswer',
    'Comment',
    'Question',
    'Observation',
    'ReviewFolder',
)


def upgrade(context):
    install_workflow(context)


def get_object(catalog, brain):
    try:
        return brain.getObject()
    except KeyError:
        logger.warn('Removing stale brain: %s', url)
        catalog.uncatalog_object(brain.getPath())


def update_permissions(content):
    for permission in PERMISSIONS:
        current_roles = [
            r['name'] for r in
            content.rolesOfPermission(permission)
            if r['selected']
        ]
        new_roles = list(set(current_roles + ['Auditor']))
        content.manage_permission(permission, roles=new_roles, acquire=0)


def reindex_or_catalog(catalog, content, url):
    try:
        content.reindexObjectSecurity()
    except KeyError:
        logger.warn('Cannot reindex. Calling catalog_object for %s!', url)
        catalog.catalog_object(content)


def update_ptype(catalog, ptype, do_reindex):
    brains = catalog(portal_type=ptype)
    brains_len = len(brains)
    for idx, brain in enumerate(brains, start=1):
        url = brain.getURL()

        content = get_object(catalog, brain)

        if content:
            update_permissions(content)
            if do_reindex:
                reindex_or_catalog(catalog, content, url)

            logger.info('Updated %s %s/%s.', url, idx, brains_len)

            if do_reindex:
                logger.info('transaction.commit after %s!', idx)
                transaction.commit()
                logger.info('gc.collect: %s!', gc.collect())


def install_workflow(context):
    setup = getToolByName(context, 'portal_setup')
    wtool = getToolByName(context, 'portal_workflow')
    catalog = getToolByName(context, 'portal_catalog')

    wtool.manage_delObjects(list(WORKFLOWS))

    setup.runImportStepFromProfile(PROFILE_ID, 'rolemap')
    setup.runImportStepFromProfile(PROFILE_ID, 'workflow')
    logger.info('Reinstalled Workflows.')

    for ptype in TYPES:
        logger.info('Updating %s!', ptype)
        do_reindex = ptype == TYPES[-1]
        update_ptype(catalog, ptype, do_reindex)

    logger.info('gc.collect: %s!', gc.collect())

