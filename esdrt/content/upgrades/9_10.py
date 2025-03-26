from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _PMF

PROFILE_ID = 'profile-esdrt.content:default'


def upgrade(context, logger=None):
    if logger is None:
        from logging import getLogger
        logger = getLogger('esdrt.content.upgrades.9_10')

    install_workflow(context, logger)
    content_types(context, logger)
    discussion_settings(context, logger)
    set_versioning(context, logger)
    css_and_js(context, logger)
    logger.info('Upgrade steps executed')


def install_workflow(context, logger):
    setup = getToolByName(context, 'portal_setup')
    wtool = getToolByName(context, 'portal_workflow')
    wtool.manage_delObjects([
        'esd-question-review-workflow',
        'esd-review-workflow',
        'esd-answer-workflow',
        'esd-comment-workflow',
        'esd-file-workflow',
        ])
    setup.runImportStepFromProfile(PROFILE_ID, 'rolemap')
    setup.runImportStepFromProfile(PROFILE_ID, 'workflow')
    setup.runImportStepFromProfile(PROFILE_ID, 'sharing')
    setup.runImportStepFromProfile(PROFILE_ID, 'typeinfo')
    logger.info('Reinstalled  Workflows')
    wtool.updateRoleMappings()
    logger.info('Security settings updated')


def content_types(context, logger):
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'typeinfo')
    setup.runImportStepFromProfile(PROFILE_ID, 'rolemap')
    setup.runImportStepFromProfile(PROFILE_ID, 'difftool')
    logger.info('Content-types reinstalled')


def discussion_settings(context, logger):
    registry = getUtility(IRegistry)
    prefix = 'plone.app.discussion.interfaces.IDiscussionSettings.'
    registry[prefix + 'globally_enabled'] = True
    registry[prefix + 'anonymous_comments'] = False
    registry[prefix + 'moderation_enabled'] = False


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
    for type_id in ['Comment', 'CommentAnswer']:
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


def css_and_js(context, logger):
    setup = getToolByName(context, 'portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'jsregistry')
    logger.info('Reload JS')
