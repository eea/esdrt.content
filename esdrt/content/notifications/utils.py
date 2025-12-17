from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from esdrt.content.constants import LDAP_BASE
from esdrt.content.setuphandlers import LDAP_PLUGIN_ID
from esdrt.content.subscriptions.interfaces import INotificationUnsubscriptions
from esdrt.content.reviewfolder import IReviewFolder
from Acquisition import aq_inner
from Acquisition import aq_parent
from cs.htmlmailer.mailer import create_html_mail
from plone import api
from Products.CMFPlone.utils import safe_unicode
from Products.statusmessages.interfaces import IStatusMessage
from zope.globalrequest import getRequest

from esdrt.content.utilities import ldap_utils


def templateWrapper(_template, _context):
    class WrappedTemplate(BrowserView):
        template = _template

        def __init__(self):
            super().__init__(_context, _context.REQUEST)

        def render(self, **options):
            return self.template(**options)


    return WrappedTemplate


def notify(observation, template: ViewPageTemplateFile, subject, role, notification_name):
    users = get_users_in_context(observation, role, notification_name)
    wrapped_template = templateWrapper(template, observation)()
    content = wrapped_template.render(observation=observation)
    send_mail(subject, safe_unicode(content), users)

def send_mail(subject, email_content, users=None):
    """
    Effectively send the e-mail message
    """
    from logging import getLogger

    log = getLogger(__name__)

    user_emails = extract_emails(users or [])
    if user_emails:
        getRequest()

        mail = create_html_mail(
            subject,
            html=email_content,
        )

        try:
            for user_addr in user_emails:
                api.portal.send_email(
                    recipient=user_addr, subject=subject, body=mail
                )
            message = "Users have been notified by e-mail"
            log.info(
                "Emails sent to users %s",
                ", ".join(
                    [email.replace("@", " <at> ") for email in user_emails]
                ),
            )
            api.portal.show_message(message)
        except Exception as e:
            message = (
                "There was an error sending the notification, "
                "but your action was completed succesfuly. "
                "Contact the EEA Secretariat for further instructions."
            )
            log.exception("Error when sending the notification!")
            api.portal.show_message(message, type="error")


def extract_emails(users):
    """
    Get the email of each user
    """
    putils = api.portal.get_tool(name='plone_utils')
    emails = []
    for user in users:
        email = user.getProperty('email')
        if email and putils.validateSingleEmailAddress(email):
            emails.append(email)

    return list(set(emails))


def get_users_in_context(observation, role, notification_name):
    users = []
    local_roles = observation.get_local_roles()

    usernames = []
    for username, userroles in local_roles:
        if role in userroles:
            group = api.group.get(username)
            if group:
                usernames.extend(group.getMemberIds())
            else:
                usernames.append(username)

    usernames = list(set(usernames))

    for username in usernames:
        user = api.user.get(username=username)
        if user is not None:
            roles = user.getRolesInContext(observation)
            step = observation.observation_phase()
            if 'phase2' in step:
                if 'ReviewerPhase1' in roles and not 'ReviewerPhase2' in roles:
                    continue
            if not exclude_user_from_notification(observation, user, role, notification_name):
                users.append(user)
        else:
            from logging import getLogger
            log = getLogger(__name__)
            log.info('Username %s has no user object' % username)

    return users


def exclude_user_from_notification(observation, user, role, notification):
    user_id = user.getId()
    adapted = INotificationUnsubscriptions(observation)
    data = adapted.get_user_data(user_id)
    if not data:
        area = aq_parent(aq_inner(observation))
        if IReviewFolder.providedBy(area):
            adapted = INotificationUnsubscriptions(area)
            data = adapted.get_user_data(user_id)
    excluded_notifications = data.get(role, [])
    exclude_based_on_notification = notification in excluded_notifications
    if exclude_based_on_notification:
        return exclude_based_on_notification

    if role in ["ReviewerPhase1", "ReviewerPhase2"] and "config_only_where_author" not in excluded_notifications:
        owner_info = observation.owner_info()
        return user_id != owner_info["id"] if owner_info and owner_info[
            "explicit"] else False


def get_ldap_group_member_ids(context, groupname):
    acl = api.portal.get()["acl_users"].get(LDAP_PLUGIN_ID)

    if acl and groupname.startswith(LDAP_BASE):
        with ldap_utils.get_query_utility()(acl) as q_ldap:
            ldap_group = q_ldap.query_groups(
                f"(cn={groupname})", ("uniqueMember",)
            )
            ldap_members = [
                x.decode() for x in ldap_group[0][1]["uniqueMember"]
            ]
            return [m.split(",")[0].split("=")[1] for m in ldap_members]
    else:
        raise ValueError
