from AccessControl import getSecurityManager
from Acquisition import aq_parent
from esdrt.content import MessageFactory as _
from five import grok
from plone.directives import dexterity
from plone.directives import form
from plone.namedfile.field import NamedBlobFile
from plone.namedfile.interfaces import IImageScaleTraversable
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import field
from zope import schema


# Interface class; used to define content-type schema.
class IESDRTFile(form.Schema, IImageScaleTraversable):
    """
    Files with special needs
    """
    title = schema.TextLine(
        title=_('Title'),
        required=False,
    )

    form.primary('file')
    file = NamedBlobFile(
        title=_('File'),
        required=True,
    )

    # confidential = schema.Bool(
    #     title=_(u'Is it a confidential file?'),
    #     description=_(u'Confidential files are only available for people '
    #                   u'taking part in the review process')
    # )


# Custom content-type class; objects created for this content type will
# be instances of this class. Use this class to add content-type specific
# methods and properties. Put methods that are mainly useful for rendering
# in separate view classes.
class ESDRTFile(dexterity.Item):
    grok.implements(IESDRTFile)
    # Add your class methods and properties here

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


class AddForm(dexterity.AddForm):
    grok.name('esdrt.content.esdrtfile')
    grok.context(IESDRTFile)
    grok.require('esdrt.content.AddESDRTFile')

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


grok.templatedir('templates')


class ESDRTFileView(grok.View):
    grok.context(IESDRTFile)
    grok.require('zope2.View')
    grok.name('view')

    def render(self):
        url = aq_parent(self.context).absolute_url()
        return self.response.redirect(url)
