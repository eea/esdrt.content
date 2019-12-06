from Acquisition import aq_parent, aq_inner
from esdrt.content import MessageFactory as _
from plone import api
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from zope.annotation.interfaces import IAnnotations
from z3c.form import button
from z3c.form import field
from z3c.form.form import Form
from zope import schema
from zope.interface import Interface
from esdrt.content.notifications.utils import notify
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from eea.cache import cache
from Products.CMFCore.utils import getToolByName
from DateTime import DateTime


def revoke_roles(username=None, user=None, obj=None, roles=None, inherit=True):
    """
    plone.api.user.revoke_roles implementation as per
    https://github.com/plone/plone.api/pull/200
    """
    if user is None:
        user = api.user.get(username=username)
    # check we got a user
    if user is None:
        raise api.InvalidParameterError("User could not be found")

    if isinstance(roles, tuple):
        roles = list(roles)

    if 'Anonymous' in roles or 'Authenticated' in roles:
        raise api.InvalidParameterError

    actual_roles = list(api.user.get_roles(user=user, obj=obj, inherit=inherit))
    if actual_roles.count('Anonymous'):
        actual_roles.remove('Anonymous')
    if actual_roles.count('Authenticated'):
        actual_roles.remove('Authenticated')

    roles = list(set(actual_roles) - set(roles))

    if obj is None:
        user.setSecurityProfile(roles=roles)
    elif not roles:
        obj.manage_delLocalRoles([user.getId()])
    else:
        obj.manage_setLocalRoles(user.getId(), roles)


class IFinishObservationReasonForm(Interface):

    comments = schema.Text(
        title=_(u'Enter comments if you want'),
        required=False,
    )


class FinishObservationReasonForm(Form):
    fields = field.Fields(IFinishObservationReasonForm)
    label = _(u'Request finalisation of the observation')
    description = _(u'Check the reason for requesting the closure of this observation')
    ignoreContext = True

    @button.buttonAndHandler(u'Request finalisation of the observation')
    def finish_observation(self, action):
        comments = self.request.get('form.widgets.comments')
        with api.env.adopt_roles(['Manager']):
            if api.content.get_state(self.context) == 'phase1-conclusions':
                self.context.closing_comments = comments
                return self.context.content_status_modify(
                    workflow_action='phase1-request-close',
                )
            elif api.content.get_state(self.context) == 'phase2-conclusions':
                self.context.closing_comments_phase2 = comments
                return self.context.content_status_modify(
                    workflow_action='phase2-finish-observation',
                )

        self.request.response.redirect(self.context.absolute_url())

    def updateWidgets(self):
        super(FinishObservationReasonForm, self).updateWidgets()
        self.widgets['comments'].rows = 15

    def updateActions(self):
        super(FinishObservationReasonForm, self).updateActions()
        for k in self.actions.keys():
            self.actions[k].addClass('standardButton')
            self.actions[k].addClass('defaultWFButton')


class IDenyFinishObservationReasonForm(Interface):

    comments = schema.Text(
        title=_(u'Enter your reasons to deny the finishing of this observation'),
        required=False,
    )


class DenyFinishObservationReasonForm(Form):
    fields = field.Fields(IDenyFinishObservationReasonForm)
    label = _(u'Deny finish observation')
    description = _(u'Check the reason for denying the finishing of this observation')
    ignoreContext = True

    @button.buttonAndHandler(u'Deny finishing observation')
    def finish_observation(self, action):
        comments = self.request.get('form.widgets.comments')
        with api.env.adopt_roles(['Manager']):
            if api.content.get_state(self.context) == 'phase1-close-requested':
                self.context.closing_deny_comments = comments
                return self.context.content_status_modify(
                    workflow_action='phase1-deny-closure',
                )
            elif api.content.get_state(self.context) == 'phase2-close-requested':
                self.context.closing_deny_comments_phase2 = comments
                return self.context.content_status_modify(
                    workflow_action='phase2-deny-finishing-observation',
                )

        return self.response.redirect(self.context.absolute_url())

    def updateWidgets(self):
        super(DenyFinishObservationReasonForm, self).updateWidgets()
        self.widgets['comments'].rows = 15

    def updateActions(self):
        super(DenyFinishObservationReasonForm, self).updateActions()
        for k in self.actions.keys():
            self.actions[k].addClass('standardButton')


class IAssignAnswererForm(Interface):
    answerers = schema.Choice(
        title=_(u'Select the answerers'),
        vocabulary=u'plone.app.vocabularies.Users',
    )

    workflow_action = schema.TextLine(
        title=_(u'Workflow action'),
        required=True
    )


class AssignAnswererForm(BrowserView):

    index = ViewPageTemplateFile('templates/assign_answerer_form.pt')

    def revoke_all_roles(self):
        """
          Revoke all existing roles
        """
        target = self.assignation_target()
        for userId, username, cp in self.get_counterpart_users():
            if cp:
                revoke_roles(
                    username=userId,
                    obj=target,
                    roles=['MSExpert'],
                    inherit=False,
                )

    def cache_get_users(fun, self, groupname):
        import time
        return (groupname, time.time() // 3600)

    @cache(cache_get_users)
    def get_users(self, groupname):
        users = api.user.get_users(groupname=groupname)
        return [(u.getId(), u.getProperty('fullname', u.getId())) for u in users]

    def assignation_target(self):
        return aq_parent(aq_inner(self.context))

    def target_groupname(self):
        context = aq_inner(self.context)
        observation = aq_parent(context)
        country = observation.country.lower()
        return 'extranet-esd-countries-msexpert-%s' % country

    def get_counterpart_users(self):
        groupname = self.target_groupname()
        current = api.user.get_current()
        current_id = current.getId()

        def isMSE(u):
            target = self.assignation_target()
            return 'MSExpert' in api.user.get_roles(username=u, obj=target, inherit=False)

        try:
            return [(u[0], u[1], isMSE(u[0])) for u in self.get_users(groupname=groupname) if current_id != u]
        except api.user.GroupNotFoundError:
            from logging import getLogger
            log = getLogger(__name__)
            log.info('There is not such a group %s' % groupname)
            return []

    def __call__(self):
        """Perform the update and redirect if necessary, or render the page
        """
        target = self.assignation_target()
        if self.request.form.get('send', None):
            usernames = self.request.get('counterparts', None)
            if not usernames:
                status = IStatusMessage(self.request)
                msg = _(u'You need to select at least one expert for discussion')
                status.addStatusMessage(msg, "error")
                return self.index()

            self.revoke_all_roles()

            for username in usernames:
                api.user.grant_roles(username=username,
                    roles=['MSExpert'],
                    obj=target)

            if api.content.get_state(self.context) in [u'phase1-pending', u'phase1-pending-answer-drafting']:
                wf_action = 'phase1-assign-answerer'
            elif api.content.get_state(self.context) in [u'phase2-pending', u'phase2-pending-answer-drafting']:
                wf_action = 'phase2-assign-answerer'
            else:
                status = IStatusMessage(self.request)
                msg = _(u'There was an error. Try again please')
                status.addStatusMessage(msg, "error")
                url = self.context.absolute_url()
                return self.request.response.redirect(url)

            return self.context.content_status_modify(
                workflow_action=wf_action,
            )

        else:
            self.revoke_all_roles()
            return self.index()


class ReAssignMSExpertsForm(AssignAnswererForm):
    def __call__(self):

        target = self.assignation_target()
        if self.request.form.get('send', None):
            usernames = self.request.get('counterparts', None)
            if not usernames:
                status = IStatusMessage(self.request)
                msg = _(u'You need to select at least one expert for discussion')
                status.addStatusMessage(msg, "error")
                return self.index()

            self.revoke_all_roles()
            for username in usernames:
                api.user.grant_roles(username=username,
                    roles=['MSExpert'],
                    obj=target)

            return self.request.response.redirect(target.absolute_url())

        else:
            return self.index()


class IAssignCounterPartForm(Interface):
    counterpart = schema.TextLine(
        title=_(u'Select the counterpart'),
    )

    workflow_action = schema.TextLine(
        title=_(u'Workflow action'),
        required=True
    )


class AssignCounterPartForm(BrowserView):

    index = ViewPageTemplateFile('templates/assign_counterpart_form.pt')

    def revoke_all_roles(self):
        """
          Revoke all existing roles
        """
        with api.env.adopt_roles(['Manager']):
            target = self.assignation_target()
            for userId, username, cp in self.get_counterpart_users():
                if cp:
                    revoke_roles(
                        username=userId,
                        obj=target,
                        roles=['CounterPart'],
                        inherit=False,
                    )

    def target_groupnames(self):
        return [
            'extranet-esd-ghginv',
            'extranet-esd-esdreview',
        ]

    def get_current_counterparters(self):
        """ Return list of current counterparters
        """
        target = self.assignation_target()
        local_roles = target.get_local_roles()
        users = [
            u[0] for u in local_roles if 'CounterPart' in u[1]
        ]
        return [api.user.get(user) for user in users]

    def cache_get_users(fun, self, groupname):
        import time
        return (groupname, time.time() // 86400)

    @cache(cache_get_users)
    def get_users(self, groupname):
        #users = api.user.get_users(groupname=groupname)
        #return [(u.getId(), u.getProperty('fullname', u.getId())) for u in users]

        vtool = getToolByName(self, 'portal_vocabularies')
        voc = vtool.getVocabularyByName(groupname)
        users = []
        voc_terms = voc.getDisplayList(self).items()
        for term in voc_terms:
            users.append((term[0], term[1]))

        return users

    def assignation_target(self):
        return aq_parent(aq_inner(self.context))

    def get_counterpart_users(self):
        current = api.user.get_current()
        current_id = current.getId()

        users = []

        target = self.assignation_target()
        local_roles = target.get_local_roles()
        counterpart_users = [
            u[0] for u in local_roles if 'CounterPart' in u[1]
        ]

        for groupname in self.target_groupnames():
            try:
                data = [
                    (u[0], u[1], u[0] in counterpart_users)
                    for u in self.get_users(groupname)
                    if current_id != u
                ]
                users.extend(data)
            except api.user.GroupNotFoundError:
                from logging import getLogger
                log = getLogger(__name__)
                log.info('There is not such a group %s' % groupname)
            except:
                from logging import getLogger
                import sys
                log = getLogger(__name__)
                log.info('Unexpected error: %s' % sys.exc_info()[0])

        return list(set(users))

    def __call__(self):
        """Perform the update and redirect if necessary, or render the page
        """
        target = self.assignation_target()
        if self.request.form.get('send', None):
            counterparts = self.request.get('counterparts', None)
            if counterparts is None:
                status = IStatusMessage(self.request)
                msg = _(u'You need to select at least one counterpart')
                status.addStatusMessage(msg, "error")
                return self.index()

            self.revoke_all_roles()

            for username in counterparts:
                api.user.grant_roles(username=username,
                    roles=['CounterPart'],
                    obj=target)

            if api.content.get_state(self.context) == 'phase1-draft':
                wf_action = 'phase1-request-for-counterpart-comments'
            elif api.content.get_state(self.context) == 'phase2-draft':
                wf_action = 'phase2-request-for-counterpart-comments'
            else:
                status = IStatusMessage(self.request)
                msg = _(u'There was an error. Try again please')
                status.addStatusMessage(msg, "error")
                url = self.context.absolute_url()
                return self.request.response.redirect(url)

            return self.context.content_status_modify(
                workflow_action=wf_action,

            )

        else:
            self.revoke_all_roles()
            return self.index()


class IAssignConclusionReviewerForm(Interface):
    reviewers = schema.Choice(
        title=_(u'Select the conclusion reviewers'),
        vocabulary=u'plone.app.vocabularies.Users',
    )


class ReAssignCounterPartForm(AssignCounterPartForm):

    index = ViewPageTemplateFile('templates/assign_counterpart_form.pt')

    def __call__(self):
        """Perform the update and redirect if necessary, or render the page
        """
        target = self.assignation_target()
        if self.request.form.get('send', None):
            counterparts = self.request.get('counterparts', None)
            if counterparts is None:
                status = IStatusMessage(self.request)
                msg = _(u'You need to select at least one counterpart')
                status.addStatusMessage(msg, "error")
                return self.index()

            self.revoke_all_roles()

            for username in counterparts:
                api.user.grant_roles(username=username,
                    roles=['CounterPart'],
                    obj=target)

            status = IStatusMessage(self.request)
            msg = _(u'CounterParts reassigned correctly')
            status.addStatusMessage(msg, "info")
            url = self.context.absolute_url()

            subject = u'New draft question to comment'
            _temp = PageTemplateFile('../notifications/question_to_counterpart.pt')
            notify(
                target,
                _temp,
                subject,
                role='CounterPart',
                notification_name='question_to_counterpart'
            )

            return self.request.response.redirect(url)

        else:
            return self.index()


class IRequestRedraftReasonForm(Interface):

    comments = schema.Text(
        title=_(u'Enter your reasons to request redraft of this question'),
        required=False,
    )


class RequestRedraftReasonForm(Form):
    fields = field.Fields(IRequestRedraftReasonForm)
    label = _(u'Ask SE to redraft')
    description = _(u'Enter your reasons to request redraft of this question')
    ignoreContext = True

    @button.buttonAndHandler(u'Ask SE to redraft')
    def request_redraft(self, action):
        comments = self.request.get('form.widgets.comments')
        with api.env.adopt_roles(['Manager']):
            cur_state = api.content.get_state(self.context)
            if cur_state.startswith('phase1'):
                self.context.request_redraft_comments = comments
                return self.context.content_status_modify(
                    workflow_action='phase1-redraft',
                )
            elif cur_state.startswith('phase2'):
                self.context.request_redraft_comments_phase2 = comments
                return self.context.content_status_modify(
                    workflow_action='phase2-redraft',
                )

        return self.response.redirect(self.context.absolute_url())

    def updateWidgets(self):
        super(RequestRedraftReasonForm, self).updateWidgets()
        self.widgets['comments'].rows = 15

    def updateActions(self):
        super(RequestRedraftReasonForm, self).updateActions()
        for k in self.actions.keys():
            self.actions[k].addClass('standardButton')


class AssignConclusionReviewerForm(BrowserView):

    index = ViewPageTemplateFile('templates/assign_conclusion_reviewer_form.pt')

    def update(self):
        self.revoke_all_roles()

    def revoke_all_roles(self):
        """
          Revoke all existing roles
        """
        target = self.assignation_target()
        for userId, username, cp in self.get_counterpart_users():
            if cp:
                revoke_roles(
                    username=userId,
                    obj=target,
                    roles=['CounterPart'],
                    inherit=False,
                )

    def cache_get_users(fun, self, groupname):
        import time
        return (groupname, time.time() // 3600)

    @cache(cache_get_users)
    def get_users(self, groupname):
        #users = api.user.get_users(groupname=groupname)
        #return [(u.getId(), u.getProperty('fullname', u.getId())) for u in users]
        vtool = getToolByName(self, 'portal_vocabularies')
        voc = vtool.getVocabularyByName(groupname)
        users = []
        voc_terms = voc.getDisplayList(self).items()
        for term in voc_terms:
            users.append((term[0], term[1]))
        return users

    def assignation_target(self):
        return aq_inner(self.context)

    def target_groupnames(self):
        return [
            'extranet-esd-ghginv',
            'extranet-esd-esdreview',
        ]

    def get_counterpart_users(self):
        current = api.user.get_current()
        current_id = current.getId()

        users = []

        target = self.assignation_target()
        local_roles = target.get_local_roles()
        counterpart_users = [
            u[0] for u in local_roles if 'CounterPart' in u[1]
        ]

        for groupname in self.target_groupnames():
            try:
                data = [
                    (u[0], u[1], u[0] in counterpart_users)
                    for u in self.get_users(groupname=groupname)
                    if current_id != u
                ]
                users.extend(data)
            except api.user.GroupNotFoundError:
                from logging import getLogger
                log = getLogger(__name__)
                log.info('There is not such a group %s' % groupname)

        return list(set(users))

    def __call__(self):
        """Perform the update and redirect if necessary, or render the page
        """
        target = self.assignation_target()
        if self.request.form.get('send', None):
            usernames = self.request.form.get('counterparts', None)
            if not usernames:
                status = IStatusMessage(self.request)
                msg = _(u'You need to select at least one reviewer for conclusions')
                status.addStatusMessage(msg, "error")
                return self.index()

            self.revoke_all_roles()

            for username in usernames:
                api.user.grant_roles(username=username,
                    obj=target,
                    roles=['CounterPart'],
                )

            if api.content.get_state(self.context).startswith('phase1-'):
                wf_action = 'phase1-request-comments'
            elif api.content.get_state(self.context).startswith('phase2-'):
                wf_action = 'phase2-request-comments'
            else:
                status = IStatusMessage(self.request)
                msg = _(u'There was an error. Try again please')
                status.addStatusMessage(msg, "error")
                url = self.context.absolute_url()
                return self.request.response.redirect(url)

            return self.context.content_status_modify(
                workflow_action=wf_action,
            )

        else:
            return self.index()

    def updateActions(self):
        super(AssignConclusionReviewerForm, self).updateActions()
        for k in self.actions.keys():
            self.actions[k].addClass('standardButton')


class UpdateWorkflow(BrowserView):
    def __call__(self):
        state_id = self.request.form.get('state_id', None)
        workflow_id = self.request.form.get('workflow_id', None)

        if not (state_id and workflow_id):
            return 'Nothing!'

        wft = self.context.portal_workflow
        workflow = wft.getWorkflowById(workflow_id)
        state_variable = workflow.state_var
        wf_state = {
            'action': None,
            'actor': None,
            'comments': "Setting state to %s" % state_id,
            state_variable: state_id,
            'time': DateTime(),
            }

        wft.setStatusOf(workflow_id, self.context, wf_state)
        workflow.updateRoleMappingsFor(self.context)

        return 'Success!'
