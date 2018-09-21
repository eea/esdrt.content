import transaction
from zope.globalrequest import getRequest
from Products.CMFCore.utils import getToolByName
import plone.api as api

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


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('esdrt.content.upgrades.55_56')
    install_workflow(context, logger)
    logger.info('Upgrade steps executed')


def install_workflow(context, logger):
    setup = getToolByName(context, 'portal_setup')
    wtool = getToolByName(context, 'portal_workflow')
    catalog = getToolByName(context, 'portal_catalog')

    wtool.manage_delObjects(list(WORKFLOWS))

    setup.runImportStepFromProfile(PROFILE_ID, 'rolemap')
    setup.runImportStepFromProfile(PROFILE_ID, 'workflow')
    logger.info('Reinstalled Workflows.')

    # make sure the Observation and ReviewFolder are indexed last.
    brains = sorted(
        catalog(portal_type=TYPES),
        key=lambda b: TYPES.index(b.portal_type)
    )
    brains_len = len(brains)

    for idx, brain in enumerate(brains, start=1):
        url = brain.getURL()
        try:
            content = brain.getObject()
        except KeyError:
            logger.warn('Removing stale brain: %s', url)
            catalog.uncatalog_object(brain.getPath())
        for permission in PERMISSIONS:
            current_roles = [
                r['name'] for r in
                content.rolesOfPermission(permission)
                if r['selected']
            ]
            new_roles = list(set(current_roles + ['Auditor']))
            content.manage_permission(permission, roles=new_roles, acquire=0)
        try:
            content.reindexObjectSecurity()
        except KeyError:
            logger.warn('Cannot reindex. Calling catalog_object for %s!', url)
            catalog.catalog_object(content)
        logger.info('Updated %s %s/%s.', url, idx, brains_len)

        if idx % 1000 == 0:
            logger.info('transaction.commit after %s!', idx)
            transaction.commit()
