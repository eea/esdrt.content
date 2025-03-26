from Products.CMFCore.utils import getToolByName
from esdrt.content.setuphandlers import prepareVocabularies

PROFILE_ID = 'profile-esdrt.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('esdrt.content.upgrades.5_6')

    reimport_vocabularies(context, logger)
    upgradeObservations(context, logger)
    install_workflow(context, logger)
    logger.info('Upgrade steps executed')


def reimport_vocabularies(context, logger):
    atvm = getToolByName(context, 'portal_vocabularies')
    del atvm['eu_member_states']
    psetup = getToolByName(context, 'portal_setup')
    profile = psetup._getImportContext(PROFILE_ID)
    prepareVocabularies(context, profile)


def upgradeObservations(context, logger):
    """ check if any observation has old country assignments
    """
    COUNTRIES = {
        'au': 'at',
        'cr': 'hr',
        'et': 'ee',
        'sv': 'sk',
    }

    brains = context.portal_catalog.unrestrictedSearchResults(
        portal_type='Observation',
        Country=list(COUNTRIES.keys()),
    )
    for brain in brains:
        observation = brain.getObject()
        old = observation.country
        new = COUNTRIES.get(old)
        observation.country = new
        logger.info('Country set for %s (%s -> %s)' % (observation.id, old, new))


def install_workflow(context, logger):
    setup = getToolByName(context, 'portal_setup')
    wtool = getToolByName(context, 'portal_workflow')
    wtool.manage_delObjects(['esd-question-review-workflow',
        'esd-review-workflow'])
    setup.runImportStepFromProfile(PROFILE_ID, 'workflow')
    logger.info('Reinstalled  Workflows')
    wtool.updateRoleMappings()
    logger.info('Security settings updated')