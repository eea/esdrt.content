from zope.globalrequest import getRequest
from Products.CMFCore.utils import getToolByName
import plone.api as api

PROFILE_ID = 'profile-esdrt.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('esdrt.content.upgrades.38_39')
    install_workflow(context, logger)
    open_observations(context, logger)
    logger.info('Upgrade steps executed')


def install_workflow(context, logger):
    setup = getToolByName(context, 'portal_setup')
    wtool = getToolByName(context, 'portal_workflow')

    wtool.manage_delObjects([
        'esd-question-review-workflow',
    ])

    setup.runImportStepFromProfile(PROFILE_ID, 'workflow')
    logger.info('Reinstalled Workflows.')

    wtool.updateRoleMappings()
    logger.info('Security settings updated')


def open_observations(context, logger):
    catalog = getToolByName(context, 'portal_catalog')
    query = dict(
        portal_type='Observation',
        review_state='phase2-draft',
    )

    def has_question(obs):
        return 'Question' in [x.portal_type for x in obs.values()]

    observations = (b.getObject() for b in catalog(**query))
    with_discussion = filter(has_question, observations)

    for observation in with_discussion:
        logger.info('Changing state for: %s', observation.absolute_url(1))
        api.content.transition(
            obj=observation,
            transition='phase2-open'
        )

    logger.info('Changed the states of %s observations.', len(with_discussion))
