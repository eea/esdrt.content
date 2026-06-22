from Acquisition import aq_inner
from Acquisition import aq_parent
from borg.localrole.interfaces import ILocalRoleProvider
from zope.component import adapter
from zope.interface import implementer

from esdrt.content.comment import IComment
from esdrt.content.commentanswer import ICommentAnswer
from esdrt.content.observation import IObservation
from esdrt.content.question import IQuestion
from esdrt.content.conclusion import IConclusion
from esdrt.content.conclusionsphase2 import IConclusionsPhase2
from plone import api


@implementer(ILocalRoleProvider)
@adapter(IObservation)
class ObservationRoleAdapter(object):

    def __init__(self, context):
        self.context = context

    def getRoles(self, principal_id):
        """Returns the roles for the given principal in context.

        This function is additional besides other ILocalRoleProvider plug-ins.

        @param context: Any Plone object
        @param principal_id: User login id
        """
        mtool = api.portal.get_tool('portal_membership')
        member = mtool.getMemberById(principal_id)
        roles = []
        if member is not None:
            context = aq_inner(self.context)
            country = context.country.lower()
            sector = context.ghg_source_category_value()
            groups = member.getGroups()
            if 'extranet-esd-ghginv-sr-%s-%s' % (sector, country) in groups:
                roles.append('ReviewerPhase1')
            if 'extranet-esd-ghginv-qualityexpert-%s' % sector in groups:
                roles.append('QualityExpert')
            if 'extranet-esd-esdreview-reviewexp-%s-%s' % (sector, country) in groups:
                roles.append('ReviewerPhase2')
            if 'extranet-esd-esdreview-leadreview-%s' % country in groups:
                roles.append('LeadReviewer')
            if 'extranet-esd-countries-msa-%s' % country in groups:
                roles.append('MSAuthority')
        if roles:
            from logging import getLogger
            log = getLogger(__name__)
            log.debug('Observation Roles: %s %s' % (principal_id, roles))

        return roles

    def getAllRoles(self):
        """Returns all the local roles assigned in this context:
        (principal_id, [role1, role2])"""
        return []


@implementer(ILocalRoleProvider)
@adapter(IQuestion)
class QuestionRoleAdapter(object):

    def __init__(self, context):
        self.context = context

    def getRoles(self, principal_id):
        """Returns the roles for the given principal in context.

        This function is additional besides other ILocalRoleProvider plug-ins.

        @param context: Any Plone object
        @param principal_id: User login id
        """
        observation = aq_parent(aq_inner(self.context))
        roles = []
        if IObservation.providedBy(observation):
            mtool = api.portal.get_tool('portal_membership')
            member = mtool.getMemberById(principal_id)
            if member is not None:
                country = observation.country.lower()
                sector = observation.ghg_source_category_value()
                groups = member.getGroups()
                if 'extranet-esd-ghginv-sr-%s-%s' % (sector, country) in groups:
                    roles.append('ReviewerPhase1')
                if 'extranet-esd-ghginv-qualityexpert-%s' % sector in groups:
                    roles.append('QualityExpert')
                if 'extranet-esd-esdreview-reviewexp-%s-%s' % (sector, country) in groups:
                    roles.append('ReviewerPhase2')
                if 'extranet-esd-esdreview-leadreview-%s' % country in groups:
                    roles.append('LeadReviewer')
                if 'extranet-esd-countries-msa-%s' % country in groups:
                    roles.append('MSAuthority')
        if roles:
            from logging import getLogger
            log = getLogger(__name__)
            log.debug('Question Roles: %s %s' % (principal_id, roles))

        return roles

    def getAllRoles(self):
        """Returns all the local roles assigned in this context:
        (principal_id, [role1, role2])"""
        return []


@implementer(ILocalRoleProvider)
@adapter(IComment)
class CommentRoleAdapter(object):

    def __init__(self, context):
        self.context = context

    def getRoles(self, principal_id):
        """Returns the roles for the given principal in context.

        This function is additional besides other ILocalRoleProvider plug-ins.

        @param context: Any Plone object
        @param principal_id: User login id
        """
        comment = aq_inner(self.context)
        question = aq_parent(comment)
        roles = []
        if IQuestion.providedBy(question):
            observation = aq_parent(question)
            if IObservation.providedBy(observation):
                mtool = api.portal.get_tool('portal_membership')
                member = mtool.getMemberById(principal_id)
                if member is not None:
                    country = observation.country.lower()
                    sector = observation.ghg_source_category_value()
                    groups = member.getGroups()
                    if 'extranet-esd-ghginv-sr-%s-%s' % (sector, country) in groups:
                        roles.append('ReviewerPhase1')
                    if 'extranet-esd-ghginv-qualityexpert-%s' % sector in groups:
                        roles.append('QualityExpert')
                    if 'extranet-esd-esdreview-reviewexp-%s-%s' % (sector, country) in groups:
                        roles.append('ReviewerPhase2')
                    if 'extranet-esd-esdreview-leadreview-%s' % country in groups:
                        roles.append('LeadReviewer')
                    if 'extranet-esd-countries-msa-%s' % country in groups:
                        roles.append('MSAuthority')

        if roles:
            from logging import getLogger
            log = getLogger(__name__)
            log.debug('Comment Roles: %s %s' % (principal_id, roles))

        return roles

    def getAllRoles(self):
        """Returns all the local roles assigned in this context:
        (principal_id, [role1, role2])"""
        return []


@implementer(ILocalRoleProvider)
@adapter(ICommentAnswer)
class CommentAnswerRoleAdapter(object):

    def __init__(self, context):
        self.context = context

    def getRoles(self, principal_id):
        """Returns the roles for the given principal in context.

        This function is additional besides other ILocalRoleProvider plug-ins.

        @param context: Any Plone object
        @param principal_id: User login id
        """
        commentanswer = aq_inner(self.context)
        question = aq_parent(commentanswer)
        roles = []
        if IQuestion.providedBy(question):
            observation = aq_parent(question)
            if IObservation.providedBy(observation):
                mtool = api.portal.get_tool('portal_membership')
                member = mtool.getMemberById(principal_id)
                if member is not None:
                    country = observation.country.lower()
                    sector = observation.ghg_source_category_value()
                    groups = member.getGroups()
                    if 'extranet-esd-ghginv-sr-%s-%s' % (sector, country) in groups:
                        roles.append('ReviewerPhase1')
                    if 'extranet-esd-ghginv-qualityexpert-%s' % sector in groups:
                        roles.append('QualityExpert')
                    if 'extranet-esd-esdreview-reviewexp-%s-%s' % (sector, country) in groups:
                        roles.append('ReviewerPhase2')
                    if 'extranet-esd-esdreview-leadreview-%s' % country in groups:
                        roles.append('LeadReviewer')
                    if 'extranet-esd-countries-msa-%s' % country in groups:
                        roles.append('MSAuthority')
        if roles:
            from logging import getLogger
            log = getLogger(__name__)
            log.debug('CommentAnswer Roles: %s %s' % (principal_id, roles))

        return roles

    def getAllRoles(self):
        """Returns all the local roles assigned in this context:
        (principal_id, [role1, role2])"""
        return []


@implementer(ILocalRoleProvider)
@adapter(IConclusion)
class ConclusionRoleAdapter(object):

    def __init__(self, context):
        self.context = context

    def getRoles(self, principal_id):
        """Returns the roles for the given principal in context.

        This function is additional besides other ILocalRoleProvider plug-ins.

        @param context: Any Plone object
        @param principal_id: User login id
        """
        observation = aq_parent(aq_inner(self.context))
        roles = []
        if IObservation.providedBy(observation):
            mtool = api.portal.get_tool('portal_membership')
            member = mtool.getMemberById(principal_id)
            if member is not None:
                country = observation.country.lower()
                sector = observation.ghg_source_category_value()
                groups = member.getGroups()
                if 'extranet-esd-ghginv-sr-%s-%s' % (sector, country) in groups:
                    roles.append('ReviewerPhase1')
                if 'extranet-esd-ghginv-qualityexpert-%s' % sector in groups:
                    roles.append('QualityExpert')
                if 'extranet-esd-esdreview-reviewexp-%s-%s' % (sector, country) in groups:
                    roles.append('ReviewerPhase2')
                if 'extranet-esd-esdreview-leadreview-%s' % country in groups:
                    roles.append('LeadReviewer')
                if 'extranet-esd-countries-msa-%s' % country in groups:
                    roles.append('MSAuthority')
        if roles:
            from logging import getLogger
            log = getLogger(__name__)
            log.debug('Conclusions Phase 1 Roles: %s %s' % (principal_id, roles))

        return roles

    def getAllRoles(self):
        """Returns all the local roles assigned in this context:
        (principal_id, [role1, role2])"""
        return []


@implementer(ILocalRoleProvider)
@adapter(IConclusionsPhase2)
class ConclusionPhase2RoleAdapter(object):

    def __init__(self, context):
        self.context = context

    def getRoles(self, principal_id):
        """Returns the roles for the given principal in context.

        This function is additional besides other ILocalRoleProvider plug-ins.

        @param context: Any Plone object
        @param principal_id: User login id
        """
        observation = aq_parent(aq_inner(self.context))
        roles = []
        if IObservation.providedBy(observation):
            mtool = api.portal.get_tool('portal_membership')
            member = mtool.getMemberById(principal_id)
            if member is not None:
                country = observation.country.lower()
                sector = observation.ghg_source_category_value()
                groups = member.getGroups()
                if 'extranet-esd-ghginv-sr-%s-%s' % (sector, country) in groups:
                    roles.append('ReviewerPhase1')
                if 'extranet-esd-ghginv-qualityexpert-%s' % sector in groups:
                    roles.append('QualityExpert')
                if 'extranet-esd-esdreview-reviewexp-%s-%s' % (sector, country) in groups:
                    roles.append('ReviewerPhase2')
                if 'extranet-esd-esdreview-leadreview-%s' % country in groups:
                    roles.append('LeadReviewer')
                if 'extranet-esd-countries-msa-%s' % country in groups:
                    roles.append('MSAuthority')
        if roles:
            from logging import getLogger
            log = getLogger(__name__)
            log.debug('Conclusions Phase 2 Roles: %s %s' % (principal_id, roles))

        return roles

    def getAllRoles(self):
        """Returns all the local roles assigned in this context:
        (principal_id, [role1, role2])"""
        return []
