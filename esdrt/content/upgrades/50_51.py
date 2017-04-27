from zope.globalrequest import getRequest
from Products.CMFCore.utils import getToolByName
import plone.api as api

PROFILE_ID = 'profile-esdrt.content:default'


STATES = (
    'phase1-counterpart-comments',
    'phase1-draft',
    'phase1-drafted',
    'phase1-recalled-lr',
    'phase2-closed',
    'phase2-draft',
    'phase2-drafted',
    'phase2-recalled-lr',
)


PERMISSION = 'Access contents information'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('esdrt.content.upgrades.50_51')
    install_workflow(context, logger)
    logger.info('Upgrade steps executed')


def install_workflow(context, logger):
    setup = getToolByName(context, 'portal_setup')
    wtool = getToolByName(context, 'portal_workflow')
    catalog = getToolByName(context, 'portal_catalog')

    wtool.manage_delObjects([
        'esd-question-review-workflow',
    ])

    setup.runImportStepFromProfile(PROFILE_ID, 'workflow')
    logger.info('Reinstalled Workflows.')

    brains = catalog(portal_type='Question', review_state=STATES)
    brains_len = len(brains)

    for idx, brain in enumerate(brains, start=1):
        content = brain.getObject()
        current_roles = [
            r['name'] for r in
            content.rolesOfPermission(PERMISSION)
            if r['selected']
        ]
        new_roles = list(set(current_roles + ['MSAuthority']))
        content.manage_permission(PERMISSION, roles=new_roles, acquire=0)
        content.reindexObjectSecurity()
        logger.info('Updated %s %s/%s.', brain.getURL(), idx, brains_len)
