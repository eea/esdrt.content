"""
    Documentation:
        -   https://github.com/tisto/collective.ploneboard/blob/master/src/collective/ploneboard/browser/commentextender.py
        -   http://plone.293351.n2.nabble.com/GSoC-2014-Collective-Ploneboard-Attachment-issue-tp7571746p7571837.html
"""
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from Acquisition import Implicit
from esdrt.content import _
from persistent import Persistent
from plone.app.discussion.browser.comments import CommentForm
from plone.app.discussion.comment import Comment
from plone.namedfile.field import NamedBlobFile
from plone.z3cform.fieldsets import extensible
from Products.CMFCore import permissions
from z3c.form.field import Fields
from zope import interface
from zope import schema
from zope.annotation import factory
from zope.component import adapts
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class ICommentExtenderFields(Interface):
    attachment = NamedBlobFile(
        title=_("Attachment"),
        description=_(""),
        required=False,
    )

    # confidential = schema.Bool(
    #     title=_(u'Is it a confidential file?'),
    #     description=_(u'Confidential files are only available for people '
    #                   u'taking part in the review process')
    # )


class CommentExtenderFields(Implicit, Persistent):
    interface.implements(ICommentExtenderFields)
    adapts(Comment)
    security = ClassSecurityInfo()

    security.declareProtected(permissions.View, 'attachment')
    attachment = ""
    #confidential = False

InitializeClass(CommentExtenderFields)

CommentExtenderFactory = factory(CommentExtenderFields)


class CommentExtender(extensible.FormExtender):
    adapts(Interface, IDefaultBrowserLayer, CommentForm)

    fields = Fields(ICommentExtenderFields)

    def __init__(self, context, request, form):
        self.context = context
        self.request = request
        self.form = form

    def update(self):
        self.add(ICommentExtenderFields, prefix="")
        self.move('attachment', after='text', prefix="")
        self.form.description = _('Handling of confidential files: '
                'Please zip your file, protect it with a password, upload it to your reply in the EEA review tool '
                'and send the password per email to the ESD Secretariat mailbox. '
                'Your password will only be shared with the lead reviewer and review expert. '
        )
