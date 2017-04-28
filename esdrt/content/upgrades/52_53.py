from zope.globalrequest import getRequest
from Products.CMFCore.utils import getToolByName
import plone.api as api

PROFILE_ID = 'profile-esdrt.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('esdrt.content.upgrades.52_53')
    install_workflow(context, logger)
    logger.info('Upgrade steps executed')


def install_workflow(context, logger):
    setup = getToolByName(context, 'portal_setup')
    wtool = getToolByName(context, 'portal_workflow')

    wtool.manage_delObjects([
        'esd-answer-workflow',
    ])

    setup.runImportStepFromProfile(PROFILE_ID, 'workflow')
    logger.info('Reinstalled Workflows.')

