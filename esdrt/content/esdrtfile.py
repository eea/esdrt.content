from AccessControl import getSecurityManager
from Acquisition import aq_parent
from Products.Five import BrowserView
from plone.dexterity.browser import add
from plone.dexterity.content import Item
from zope.interface import implementer

from esdrt.content import _
from plone.supermodel.directives import primary
from plone.supermodel import model
from plone.namedfile.field import NamedBlobFile
from plone.namedfile.interfaces import IImageScaleTraversable
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import field
from zope import schema


# Interface class; used to define content-type schema.
class IESDRTFile(model.Schema, IImageScaleTraversable):
    """
    Files with special needs
    """
    title = schema.TextLine(
        title=_('Title'),
        required=False,
    )

    primary('file')
    file = NamedBlobFile(
        title=_('File'),
        required=True,
    )

    # confidential = schema.Bool(
    #     title=_(u'Is it a confidential file?'),
    #     description=_(u'Confidential files are only available for people '
    #                   u'taking part in the review process')
    # )


@implementer(IESDRTFile)
class ESDRTFile(Item):

    def can_edit(self):
        sm = getSecurityManager()
        parent = aq_parent(self)
        edit = False
        if parent.portal_type == 'Comment':
            edit = sm.checkPermission('esdrt.content: Edit Comment', self)
        elif parent.portal_type == 'CommentAnswer':
            edit = sm.checkPermission('esdrt.content: Edit CommentAnswer', self)
        elif parent.portal_type in 'Conclusion':
            edit = sm.checkPermission('Modify portal content', self)
        return edit


class AddForm(add.DefaultAddForm):

    label = 'file'
    description = ''

    def update(self):
        super(AddForm, self).update()
        status = IStatusMessage(self.request)

        msg = _('Handling of confidential files: '
                'Please zip your file, protect it with a password, upload it to your reply in the EEA review tool '
                'and send the password per email to the ESD Secretariat mailbox. '
                'Your password will only be shared with the lead reviewer and review expert. '
        )

        status.add(msg, type='info')

    def updateFields(self):
        super(AddForm, self).updateFields()
        self.fields = field.Fields(IESDRTFile).omit('title')
        self.groups = [g for g in self.groups if g.label == 'label_schema_default']


class AddView(add.DefaultAddView):
    form = AddForm


class ESDRTFileView(BrowserView):

    def render(self):
        url = aq_parent(self.context).absolute_url()
        return self.response.redirect(url)
