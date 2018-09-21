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

    brains = catalog(portal_type=TYPES)
    brains_len = len(brains)

    for idx, brain in enumerate(brains, start=1):
        content = brain.getObject()
        for permission in PERMISSIONS:
            current_roles = [
                r['name'] for r in
                content.rolesOfPermission(permission)
                if r['selected']
            ]
            new_roles = list(set(current_roles + ['Auditor']))
            content.manage_permission(permission, roles=new_roles, acquire=0)
        content.reindexObjectSecurity()
        logger.info('Updated %s %s/%s.', brain.getURL(), idx, brains_len)

