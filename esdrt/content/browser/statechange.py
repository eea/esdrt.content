import re
from functools import partial
from operator import itemgetter

from App.config import getConfiguration
from Acquisition import aq_parent, aq_inner
from esdrt.content import _
from plone import api
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from z3c.form import field
from z3c.form.form import Form
from zope import schema
from zope.interface import Interface

from esdrt.content.constants import LDAP_MSE
from esdrt.content.constants import ROLE_CP
from esdrt.content.constants import ROLE_MSE
from esdrt.content.notifications.utils import get_ldap_group_member_ids
from esdrt.content.notifications.utils import notify
from Products.Five.browser.pagetemplatefile import PageTemplateFile
from plone.memoize.ram import cache
from Products.CMFCore.utils import getToolByName
from DateTime import DateTime

from esdrt.content.reviewfolder import IReviewFolder
from esdrt.content.utils import find_parent_with_interface

TEST_USERS = ("sectorrev", "reviewsec", )

PARENT_REVIEWFOLDER = partial(find_parent_with_interface, IReviewFolder)

RE_EXTRACT_SECTOR_COUNTRY = re.compile(r"(sector\d)?-([a-z]{2})$")


def group_matches_sector_and_country(name, pass_sector, pass_country):
    """If neither sector nor country is found in the group name,
    validate it as True in order to cover lead groups.
    """
    sector, country = RE_EXTRACT_SECTOR_COUNTRY.search(name).groups()
    result = []
    if sector:
        result.append(sector == pass_sector)
    if country:
        result.append(country == pass_country)

    return all(result) if result else True


def filter_groups_for_context(context, names):
    validate_group = partial(
        group_matches_sector_and_country,
        pass_sector=context.ghg_source_category_value(),
        pass_country=context.country,
    )
    return tuple(filter(validate_group, names))


def exclude_test_users(userdata):
    """Filter out test user ids if not in development mode."""
    if getConfiguration().debug_mode:
        return userdata

    userid = itemgetter(0)

    def drop(data):
        return not tuple(ex for ex in TEST_USERS if ex in userid(data))

    return list(filter(drop, userdata))


class IFinishObservationReasonForm(Interface):

    comments = schema.Text(
        title=_('Enter comments if you want'),
        required=False,
    )


class FinishObservationReasonForm(Form):
    fields = field.Fields(IFinishObservationReasonForm)
    label = _('Request finalisation of the observation')
    description = _('Check the reason for requesting the closure of this observation')
    ignoreContext = True

    @button.buttonAndHandler('Request finalisation of the observation')
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
        for k in list(self.actions.keys()):
            self.actions[k].addClass('standardButton')
            self.actions[k].addClass('defaultWFButton')


class IDenyFinishObservationReasonForm(Interface):

    comments = schema.Text(
        title=_('Enter your reasons to deny the finishing of this observation'),
        required=False,
    )


class DenyFinishObservationReasonForm(Form):
    fields = field.Fields(IDenyFinishObservationReasonForm)
    label = _('Deny finish observation')
    description = _('Check the reason for denying the finishing of this observation')
    ignoreContext = True

    @button.buttonAndHandler('Deny finishing observation')
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
        for k in list(self.actions.keys()):
            self.actions[k].addClass('standardButton')


class AssignFormMixin(BrowserView):
    index = None

    _managed_role = None

    _revoke_on_call = None

    _msg_no_usernames = None

    def show_test_users(self):
        user = api.user.get_current()

        return (
            any(usr in user.getUserName() for usr in TEST_USERS)
            or "Manager" in user.getRoles()
        )

    def _get_wf_action(self):
        raise NotImplementedError

    def _assignation_target(self):
        raise NotImplementedError

    def _target_groupnames(self):
        raise NotImplementedError

    def _extra_usernames(self, target):
        return []

    def _is_managed_role(self, username):
        return self._managed_role in api.user.get_roles(
            username=username, obj=self._assignation_target(), inherit=False
        )

    def revoke_all_roles(self):
        with api.env.adopt_roles(["Manager"]):
            target = self._assignation_target()
            for userId, username, cp in self.get_counterpart_users(False):
                if cp:
                    api.user.revoke_roles(
                        username=userId,
                        obj=target,
                        roles=[self._managed_role],
                    )

    def get_counterpart_users(self, exclude_test=True):
        users = []

        if self.show_test_users():
            exclude_test = False

        current_user_id = api.user.get_current().getId()

        for group_id in self._target_groupnames():
            group_member_ids = get_ldap_group_member_ids(
                self.context, group_id
            )
            for user_id in group_member_ids:
                if user_id != current_user_id:
                    user = api.user.get(username=user_id)
                    users.append(
                        (
                            user_id,
                            user.getProperty("fullname"),
                            self._is_managed_role(user_id),
                        )
                    )

        result = list(set(users))

        if exclude_test:
            return exclude_test_users(result)
        else:
            return result

    def __call__(self):
        """Perform the update and redirect if necessary, or render the page."""
        target = self._assignation_target()
        if self.request.get("send", None):
            usernames = self.request.get("counterparts", None)
            if not usernames:
                msg = self._msg_no_usernames
                api.portal.show_message(message=msg, type="error")
                return self.index()

            self.revoke_all_roles()

            usernames.extend(self._extra_usernames(target))
            for username in usernames:
                api.user.grant_roles(
                    username=username, roles=[self._managed_role], obj=target
                )

            target.reindexObjectSecurity()

            wf_action = self._get_wf_action()
            if wf_action:
                api.content.transition(obj=self.context, transition=wf_action)
            else:
                msg = _("There was an error. Try again please")
                api.portal.show_message(message=msg, type="error")

            url = self.context.absolute_url()
            return self.request.response.redirect(url)

        else:
            if self._revoke_on_call:
                self.revoke_all_roles()
            return self.index()




class IAssignAnswererForm(Interface):
    answerers = schema.Choice(
        title=_('Select the answerers'),
        vocabulary='plone.app.vocabularies.Users',
    )

    workflow_action = schema.TextLine(
        title=_('Workflow action'),
        required=True
    )



class AssignAnswererForm(AssignFormMixin):
    index = ViewPageTemplateFile("templates/assign_answerer_form.pt")

    _managed_role = ROLE_MSE
    _revoke_on_call = True
    _msg_no_usernames = _(
        "You need to select at least one expert for discussion"
    )

    def _assignation_target(self):
        return aq_parent(aq_inner(self.context))

    def _extra_usernames(self, target):
        country = target.country
        return ["necd_eea_{}_exp".format(country)]

    def _target_groupnames(self):
        context = aq_inner(self.context)
        observation = aq_parent(context)
        country = observation.country.lower()
        return [f"{LDAP_MSE}-{country}"]

    def _get_wf_action(self):
        if api.content.get_state(self.context) in ['phase1-pending', 'phase1-carried-over', 'phase1-pending-answer-drafting', 'phase1-recalled-msa']:
            return 'phase1-assign-answerer'
        elif api.content.get_state(self.context) in ['phase2-pending', 'phase2-carried-over', 'phase2-pending-answer-drafting', 'phase2-recalled-msa']:
            return 'phase2-assign-answerer'


class ReAssignMSExpertsForm(AssignAnswererForm):
    def __call__(self):
        target = self._assignation_target()
        if self.request.form.get("send", None):
            usernames = self.request.get("counterparts", None)
            if not usernames:
                status = IStatusMessage(self.request)
                msg = _(
                    "You need to select at least one expert for discussion"
                )
                status.addStatusMessage(msg, "error")
                return self.index()

            self.revoke_all_roles()

            usernames.extend(self._extra_usernames(target))
            for username in usernames:
                api.user.grant_roles(
                    username=username, roles=[self._managed_role], obj=target
                )
            target.reindexObjectSecurity()

            # TODO: uncomment after notifications refactoring
            # answer_to_msexperts.notification_mse(self.context, reassign=True)

            return self.request.response.redirect(target.absolute_url())

        else:
            return self.index()


class IAssignCounterPartForm(Interface):
    counterpart = schema.TextLine(
        title=_('Select the counterpart'),
    )

    workflow_action = schema.TextLine(
        title=_('Workflow action'),
        required=True
    )


class AssignCounterPartForm(AssignFormMixin):
    index = ViewPageTemplateFile("templates/assign_counterpart_form.pt")

    _managed_role = ROLE_CP
    _revoke_on_call = True
    _msg_no_usernames = _("You need to select at least one counterpart")

    def _assignation_target(self):
        return aq_parent(aq_inner(self.context))

    def _get_wf_action(self):
        if api.content.get_state(self.context) == 'phase1-draft':
            return 'phase1-request-for-counterpart-comments'
        elif api.content.get_state(self.context) == 'phase2-draft':
            return 'phase2-request-for-counterpart-comments'

    def _target_groupnames(self):
        return [
            'extranet-esd-ghginv',
            'extranet-esd-esdreview',
        ]

    def get_current_counterparters(self):
        """Return list of current counterparters."""
        target = self._assignation_target()
        local_roles = target.get_local_roles()
        users = [u[0] for u in local_roles if self._managed_role in u[1]]

        skipped_extra_users = self._extra_usernames(target)
        return [
            api.user.get(user)
            for user in users
            if user not in skipped_extra_users
        ]


class IAssignConclusionReviewerForm(Interface):
    reviewers = schema.Choice(
        title=_('Select the conclusion reviewers'),
        vocabulary='plone.app.vocabularies.Users',
    )


class ReAssignCounterPartForm(AssignCounterPartForm):

    index = ViewPageTemplateFile('templates/assign_counterpart_form.pt')

    def __call__(self):
        """Perform the update and redirect if necessary, or render the page
        """
        target = self._assignation_target()
        if self.request.form.get('send', None):
            counterparts = self.request.get('counterparts', None)
            if counterparts is None:
                status = IStatusMessage(self.request)
                msg = self._msg_no_usernames
                status.addStatusMessage(msg, "error")
                return self.index()

            self.revoke_all_roles()

            for username in counterparts:
                api.user.grant_roles(
                    username=username, roles=[self._managed_role], obj=target
                )

            target.reindexObjectSecurity()

            status = IStatusMessage(self.request)
            msg = _('CounterParts reassigned correctly')
            status.addStatusMessage(msg, "info")
            url = self.context.absolute_url()

            subject = 'New draft question to comment'
            _temp = PageTemplateFile('../notifications/question_to_counterpart.pt')
            notify(
                target,
                _temp,
                subject,
                role='CounterPart',
                notification_name='question_to_counterpart'
            )

            # TODO: uncomment after notifications refactoring
            # question_to_counterpart.notification_cp(
            #     self.context, reassign=True
            # )

            return self.request.response.redirect(url)

        else:
            return self.index()


class IRequestRedraftReasonForm(Interface):

    comments = schema.Text(
        title=_('Enter your reasons to request redraft of this question'),
        required=False,
    )


class RequestRedraftReasonForm(Form):
    fields = field.Fields(IRequestRedraftReasonForm)
    label = _('Ask SE to redraft')
    description = _('Enter your reasons to request redraft of this question')
    ignoreContext = True

    @button.buttonAndHandler('Ask SE to redraft')
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
        for k in list(self.actions.keys()):
            self.actions[k].addClass('standardButton')


class AssignConclusionReviewerForm(AssignFormMixin):
    index = ViewPageTemplateFile(
        "templates/assign_conclusion_reviewer_form.pt"
    )

    _managed_role = ROLE_CP
    _revoke_on_call = False
    _msg_no_usernames = _(
        "You need to select at least one reviewer for conclusions"
    )

    def update(self):
        self.revoke_all_roles()

    def _assignation_target(self):
        return aq_inner(self.context)

    def _target_groupnames(self):
        return [
            'extranet-esd-ghginv',
            'extranet-esd-esdreview',
        ]

    def _get_wf_action(self):
        if api.content.get_state(self.context).startswith('phase1-'):
            return 'phase1-request-comments'
        elif api.content.get_state(self.context).startswith('phase2-'):
            return 'phase2-request-comments'


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
