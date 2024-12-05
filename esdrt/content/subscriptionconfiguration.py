from plone import api
from Products.statusmessages.interfaces import IStatusMessage
from five import grok
from Acquisition import aq_inner
from Acquisition import aq_parent
from AccessControl import Unauthorized
from plone.memoize.view import memoize
from .observation import IObservation
from .observation import ObservationView
from .reviewfolder import IReviewFolder
from esdrt.content.subscriptions.interfaces import INotificationUnsubscriptions
from esdrt.content.subscriptions.dexterity import UNSUBSCRIPTION_KEY
from BTrees.OOBTree import OOBTree
from zope.annotation.interfaces import IAnnotations

import copy

ROLE_TRANSLATOR = {
    'ReviewerPhase1': 'Sector Expert (phase 1)',
    'ReviewerPhase2': 'Review Expert (phase 2)',
    'QualityExpert':  'Quality Expert (phase 1)',
    'LeadReviewer':   'Lead Reviewer (phase 2)',
    'MSAuthority':    'Member State Coordinator',
    'CounterPart':    'Counter Part',
    'MSExpert':       'Member State Expert',
}


NOTIFICATIONS_PER_ROLE = {
    'ReviewerPhase1': {
        'observation_finalisation_denied': True,
        'observation_finalised': True,
        'question_answered': True,
        'question_to_ms': True,
        'config_only_where_author': True,
    },
    'ReviewerPhase2': {
        'observation_finalisation_denied': True,
        'observation_finalised': True,
        'observation_to_phase2': True,
        'question_answered': True,
        'question_to_ms': True,
        'config_only_where_author': True,
    },
    'QualityExpert': {
        'conclusion_to_comment': True,
        'observation_finalisation_request': True,
        'question_answered': True,
        'question_ready_for_approval': True,
        'question_to_counterpart': True,
    },
    'LeadReviewer': {
        'conclusion_to_comment': True,
        'observation_finalisation_request': True,
        'observation_to_phase2': True,
        'question_answered': True,
        'question_ready_for_approval': True,
        'question_to_counterpart': True,
    },
    'MSAuthority': {
        'answer_acknowledged': True,
        'observation_finalised': True,
        'question_to_ms': True,
    },
    'CounterPart': {
        'conclusion_to_comment': True,
        'question_to_counterpart': True,
    },
    'MSExpert': {
        'answer_to_msexperts': True,
        'question_answered': True,
    },
}

NOTIFICATION_NAMES = {
    'ReviewerPhase1': {
        'observation_finalisation_denied': 'Observation finalisation denied by QE',
        'observation_finalised': 'Observation finalised by QE',
        'question_answered': 'Question answered by MS',
        'question_to_ms': 'Question sent to MS by QE',
        'config_only_where_author': 'Only notify me about observations I authored',
    },
    'ReviewerPhase2': {
        'observation_finalisation_denied': 'Observation finalisation denied by LR',
        'observation_finalised': 'Observation finalised by LR',
        'observation_to_phase2': 'Observation handed over to step 2',
        'question_answered': 'Question answered by MS',
        'question_to_ms': 'Question sent to MS by LR',
        'config_only_where_author': 'Only notify me about observations I authored',
    },
    'QualityExpert': {
        'conclusion_to_comment': 'Conclusion to comment by you as QE',
        'observation_finalisation_request': 'Observation finalisation ready for your approval as QE',
        'question_answered': 'Question answered by MS',
        'question_ready_for_approval': 'Question ready for your approval as QE',
        'question_to_counterpart': 'Question to comment by you as QE',
    },
    'LeadReviewer': {
        'conclusion_to_comment': 'Conclusion to comment by you as LR',
        'observation_finalisation_request': 'Observation finalisation ready for your approval as LR',
        'observation_to_phase2': 'Observation handed over to step 2',
        'question_answered': 'Question answered by MS',
        'question_ready_for_approval': 'Question ready for your approval as LR',
        'question_to_counterpart': 'Question to comment by you as LR',
    },
    'MSAuthority': {
        'answer_acknowledged': 'Answer acknowledged by sector expert',
        'observation_finalised': 'Observation finished by Quality Expert',
        'question_to_ms': 'Question to be answered by your country',
    },
    'CounterPart': {
        'conclusion_to_comment': 'Conclusion to comment by you as counterpart',
        'question_to_counterpart': 'Question to comment by you as counterpart',
    },
    'MSExpert': {
        'answer_to_msexperts': 'New question to comment by you as MS expert',
        'question_answered': 'Question answered by MS',
    }
}


grok.templatedir('templates')


class SubscriptionConfigurationMixin(grok.View):
    grok.baseclass()

    @memoize
    def user(self):
        if api.user.is_anonymous():
            raise Unauthorized
        return api.user.get_current()

    def user_roles(self, context=None, translated_roles=True):
        if context is None:
            context = self.context

        user = self.user()
        roles = []
        for role in api.user.get_roles(user=user, obj=context):
            if translated_roles:
                translated = ROLE_TRANSLATOR.get(role)
                if translated is not None:
                    roles.append(translated)
            else:
                if role in ROLE_TRANSLATOR.keys():
                    roles.append(role)
        return roles

    def get_unsubscribed_notifications(self, context=None):
        if context is None:
            context = self.context

        if not(
            IReviewFolder.providedBy(context) or IObservation.providedBy(context)
        ):
            return {}

        user = self.user()
        adapted = INotificationUnsubscriptions(context)
        data = adapted.get_user_data(user.getId())

        if IReviewFolder.providedBy(context):
            return data

        if not data:
            parent = aq_parent(aq_inner(context))
            return self.get_unsubscribed_notifications(context=parent)

        return data


    def my_subscriptions(self):
        roles = []

        roles = self.user_roles(translated_roles=False)

        unsubscribed_notifications = self.get_unsubscribed_notifications()

        items = {}
        for role in roles:
            data = copy.copy(NOTIFICATIONS_PER_ROLE.get(role))
            for unsubscribed in unsubscribed_notifications.get(role, []):
                data[unsubscribed] = False

            items[role] = data
        return items

    def notification_name(self, rolename, notification_name):
        return NOTIFICATION_NAMES.get(rolename, {}).get(
            notification_name, notification_name
        )

    def translate_rolename(self, rolename):
        return ROLE_TRANSLATOR.get(rolename, rolename)


class SubscriptionConfigurationReview(SubscriptionConfigurationMixin):
    grok.context(IReviewFolder)
    grok.name('subscription-configuration')
    grok.require('zope2.View')


class SubscriptionConfiguration(SubscriptionConfigurationReview, ObservationView):
    grok.context(IObservation)

    def has_local_notifications_settings(self):
        user = api.user.get_current()
        adapted = INotificationUnsubscriptions(self.context)
        data = adapted.get_user_data(user.getId())

        return data and True or False


class SaveSubscriptionsReview(SubscriptionConfigurationMixin):
    grok.context(IReviewFolder)
    grok.require('zope2.View')
    grok.name('save-subscriptions')



    def render(self):
        user_roles = []
        if self.request.get('REQUEST_METHOD') == 'POST':
            user = self.user()
            data = self.request.get('subscription_data')
            adapted = INotificationUnsubscriptions(self.context)
            user_roles = self.user_roles(translated_roles=False)
            to_delete = {}
            for item in data:
                copied_item = dict(item)
                rolename = copied_item.get('name')
                del copied_item['name']
                if rolename in user_roles:
                    notifications = set(NOTIFICATIONS_PER_ROLE.get(rolename))
                    deleted = notifications.difference(set(copied_item.keys()))
                    to_delete[rolename] = deleted

            adapted.unsubscribe(user.getId(), notifications=to_delete)
            status = IStatusMessage(self.request)
            status.add('Subscription preferences saved correctly', type='info')
            url = self.context.absolute_url()
            return self.request.response.redirect(url)

        status = IStatusMessage(self.request)
        status.add('There was an error', type='error')
        return self.request.response.redirect(self.context.absolute_url())


class SaveSubscriptions(SaveSubscriptionsReview):
    grok.context(IObservation)


class ClearSubscriptions(SubscriptionConfigurationMixin):
    grok.context(IObservation)
    grok.require('zope2.View')
    grok.name('clear-subscriptions')

    def render(self):
        user = self.user()
        adapted = INotificationUnsubscriptions(self.context)
        adapted.unsubscribe(user.getId())

        status = IStatusMessage(self.request)
        status.add('Local subscription preferences cleared', type='info')
        return self.request.response.redirect(self.context.absolute_url())
