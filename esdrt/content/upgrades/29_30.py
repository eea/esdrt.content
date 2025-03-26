from Products.CMFCore.utils import getToolByName
from esdrt.content.setuphandlers import prepareVocabularies
from Products.CMFPlone import PloneMessageFactory as _PMF

PROFILE_ID = 'profile-esdrt.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('esdrt.content.upgrades.29_30')

    install_workflow(context, logger)
    reimport_vocabularies(context, logger)
    set_versioning(context, logger)
    logger.info('Upgrade steps executed')


def reimport_vocabularies(context, logger):
    atvm = getToolByName(context, 'portal_vocabularies')
    del atvm['conclusion_reasons']
    del atvm['conclusion_phase2_reasons']
    psetup = getToolByName(context, 'portal_setup')
    profile = psetup._getImportContext(PROFILE_ID)
    prepareVocabularies(context, profile)


def install_workflow(context, logger):
    setup = getToolByName(context, 'portal_setup')
    wtool = getToolByName(context, 'portal_workflow')
    wtool.manage_delObjects([
        'esd-answer-workflow',
        'esd-comment-workflow',
        'esd-conclusion-workflow',
        'esd-conclusion-phase2-workflow',
        'esd-file-workflow',
        'esd-question-review-workflow',
        'esd-reviewtool-folder-workflow',
        'esd-review-workflow',
    ])

    setup.runImportStepFromProfile(PROFILE_ID, 'rolemap')
    setup.runImportStepFromProfile(PROFILE_ID, 'workflow')
    setup.runImportStepFromProfile(PROFILE_ID, 'sharing')
    logger.info('Reinstalled Workflows, Roles and Permissions ')
    wtool.updateRoleMappings()
    logger.info('Security settings updated')

VERSION_POLICIES = [
    dict(id="off",
         policy=(),
         title=_PMF("versioning_off",
                 default="No versioning")),

    dict(id="manual",
         policy=("version_on_revert",),
         title=_PMF("versioning_manual",
                 default="Manual")),

    dict(id="automatic",
         policy=("at_edit_autoversion", "version_on_revert"),
         title=_PMF("versioning_automatic",
                 default="Automatic")),
]


def set_versioning(context, logger):
    version_policy = 'automatic'
    portal_repository = getToolByName(context, 'portal_repository')
    newpolicy = [p for p in VERSION_POLICIES if p["id"] == version_policy][0]
    versionable_types = list(portal_repository.getVersionableContentTypes())
    for type_id in ['Conclusion', 'ConclusionsPhase2']:
        if not newpolicy["policy"]:
            if type_id in versionable_types:
                versionable_types.remove(type_id)
        else:
            if type_id not in versionable_types:
                versionable_types.append(type_id)

        for policy in portal_repository.listPolicies():
            policy_id = policy.getId()
            if policy_id in newpolicy["policy"]:
                portal_repository.addPolicyForContentType(type_id, policy_id)
            else:
                portal_repository.removePolicyFromContentType(type_id,
                    policy_id)

    portal_repository.setVersionableContentTypes(versionable_types)
