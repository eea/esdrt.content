from AccessControl import getSecurityManager
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from Acquisition.interfaces import IAcquirer
from esdrt.content import MessageFactory as _
from five import grok
from plone import api
from plone.dexterity.interfaces import IDexterityFTI
from plone.directives import dexterity
from plone.directives import form
from plone.namedfile.interfaces import IImageScaleTraversable
from time import time
from z3c.form import field
from zope.component import createObject
from zope.component import getUtility
from zope import schema

# Interface class; used to define content-type schema.
class ICommentAnswer(form.Schema, IImageScaleTraversable):
    """
    Answer for Questions
    """
    # If you want a schema-defined interface, delete the form.model
    # line below and delete the matching file in the models sub-directory.
    # If you want a model-based interface, edit
    # models/comment.xml to define the content type
    # and add directives here as necessary.
    text = schema.Text(
        title=_('Text'),
        required=True,
    )


# Custom content-type class; objects created for this content type will
# be instances of this class. Use this class to add content-type specific
# methods and properties. Put methods that are mainly useful for rendering
# in separate view classes.
class CommentAnswer(dexterity.Container):
    grok.implements(ICommentAnswer)
    # Add your class methods and properties here

    def can_edit(self):
        sm = getSecurityManager()
        return sm.checkPermission('esdrt.content: Edit CommentAnswer', self)

    def can_add_files(self):
        sm = getSecurityManager()
        parent = aq_parent(self)
        return sm.checkPermission('esdrt.content: Add ESDRTFile', self) and api.content.get_state(parent) not in ['phase1-expert-comments', 'phase2-expert-comments']

    def get_files(self):
        items = list(self.values())
        mtool = api.portal.get_tool('portal_membership')
        return [item for item in items if mtool.checkPermission('View', item)]

    def can_delete(self):
        sm = getSecurityManager()
        parent = aq_parent(self)
        parent_state = api.content.get_state(parent)
        return sm.checkPermission('Delete portal content', self) and parent_state not in ['phase1-expert-comments', 'phase2-expert-comments']


# View class
# The view will automatically use a similarly named template in
# templates called commentanswerview.pt .
# Template filenames should be all lower case.
# The view will render when you request a content object with this
# interface with "/@@view" appended unless specified otherwise
# using grok.name below.
# This will make this view the default view for your content-type
grok.templatedir('templates')


class CommentAnswerView(grok.View):
    grok.context(ICommentAnswer)
    grok.require('zope2.View')
    grok.name('view')

    def render(self):
        context = aq_inner(self.context)
        parent = aq_parent(context)
        url = '%s#%s' % (parent.absolute_url(), context.getId())

        return self.request.response.redirect(url)


class AddForm(dexterity.AddForm):
    grok.name('esdrt.content.commentanswer')
    grok.context(ICommentAnswer)
    grok.require('esdrt.content.AddCommentAnswer')

    label = 'Answer'
    description = ''

    def updateFields(self):
        super(AddForm, self).updateFields()
        self.fields = field.Fields(ICommentAnswer).select('text')
        self.groups = [g for g in self.groups if g.label == 'label_schema_default']

    def updateWidgets(self):
        super(AddForm, self).updateWidgets()
        self.widgets['text'].rows = 15

    def create(self, data={}):
        # import pdb; pdb.set_trace()
        # return super(AddForm, self).create(data)
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        container = aq_inner(self.context)
        content = createObject(fti.factory)
        if hasattr(content, '_setPortalTypeName'):
            content._setPortalTypeName(fti.getId())

        # Acquisition wrap temporarily to satisfy things like vocabularies
        # depending on tools
        if IAcquirer.providedBy(content):
            content = content.__of__(container)

        id = str(int(time()))
        content.title = id
        content.id = id
        content.text = self.request.form.get('form.widgets.text', '')

        return aq_base(content)


class EditForm(dexterity.EditForm):
    grok.name('edit')
    grok.context(ICommentAnswer)
    grok.require('esdrt.content.EditCommentAnswer')

    label = 'Answer'
    description = ''

    def updateFields(self):
        super(EditForm, self).updateFields()
        self.fields = field.Fields(ICommentAnswer).select('text')
        self.groups = [g for g in self.groups if g.label == 'label_schema_default']

    def updateWidgets(self):
        super(EditForm, self).updateWidgets()
        self.widgets['text'].rows = 15

    def updateActions(self):
        super(EditForm, self).updateActions()
        for k in list(self.actions.keys()):
            self.actions[k].addClass('standardButton')
