from time import time

from AccessControl import getSecurityManager
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from Acquisition.interfaces import IAcquirer
from five import grok
from plone import api
from plone.dexterity.interfaces import IDexterityFTI
from plone.directives import dexterity
from plone.directives import form
from plone.namedfile.interfaces import IImageScaleTraversable
from z3c.form import field
from zope import schema
from zope.app.container.interfaces import IObjectAddedEvent
from zope.component import createObject
from zope.component import getUtility

from esdrt.content import MessageFactory as _


# Interface class; used to define content-type schema.
class IComment(form.Schema, IImageScaleTraversable):
    """
    Q&A item
    """
    # If you want a schema-defined interface, delete the form.model
    # line below and delete the matching file in the models sub-directory.
    # If you want a model-based interface, edit
    # models/comment.xml to define the content type
    # and add directives here as necessary.
    text = schema.Text(
        title=_(u'Text'),
        required=True,
    )


# Custom content-type class; objects created for this content type will
# be instances of this class. Use this class to add content-type specific
# methods and properties. Put methods that are mainly useful for rendering
# in separate view classes.
class Comment(dexterity.Container):
    grok.implements(IComment)

    # Add your class methods and properties here

    def can_edit(self):
        sm = getSecurityManager()
        return sm.checkPermission('esdrt.content: Edit Comment', self)

    def can_delete(self):
        sm = getSecurityManager()
        return sm.checkPermission('Delete portal content', self)

    def can_add_files(self):
        sm = getSecurityManager()
        return sm.checkPermission('esdrt.content: Add ESDRTFile', self)

    def get_files(self):
        items = self.values()
        mtool = api.portal.get_tool('portal_membership')
        return [item for item in items if mtool.checkPermission('View', item)]


# View class
# The view will automatically use a similarly named template in
# templates called commentview.pt .
# Template filenames should be all lower case.
# The view will render when you request a content object with this
# interface with "/@@view" appended unless specified otherwise
# using grok.name below.
# This will make this view the default view for your content-type
grok.templatedir('templates')


class CommentView(grok.View):
    grok.context(IComment)
    grok.require('zope2.View')
    grok.name('view')

    def render(self):
        context = aq_inner(self.context)
        parent = aq_parent(context)
        url = '%s#%s' % (parent.absolute_url(), context.getId())

        return self.request.response.redirect(url)


class AddForm(dexterity.AddForm):
    grok.name('esdrt.content.comment')
    grok.context(IComment)
    grok.require('esdrt.content.AddComment')

    label = 'Question'
    description = ''

    def updateFields(self):
        super(AddForm, self).updateFields()
        self.fields = field.Fields(IComment).select('text')
        self.groups = [g for g in self.groups if
                       g.label == 'label_schema_default']

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

    def updateActions(self):
        super(AddForm, self).updateActions()
        for k in self.actions.keys():
            self.actions[k].addClass('standardButton')


class EditForm(dexterity.EditForm):
    grok.name('edit')
    grok.context(IComment)
    grok.require('esdrt.content.EditComment')

    label = 'Question'
    description = ''

    def updateFields(self):
        super(EditForm, self).updateFields()
        self.fields = field.Fields(IComment).select('text')
        self.groups = [g for g in self.groups if
                       g.label == 'label_schema_default']

    def updateWidgets(self):
        super(EditForm, self).updateWidgets()
        self.widgets['text'].rows = 15

    def updateActions(self):
        super(EditForm, self).updateActions()
        for k in self.actions.keys():
            self.actions[k].addClass('standardButton')


@grok.subscribe(IComment, IObjectAddedEvent)
def add_question(context, event):
    """ When adding a question, go directly to
        'open' status on the observation
    """
    question = aq_parent(context)
    observation = aq_parent(question)
    with api.env.adopt_roles(roles=['Manager']):
        # XXX: This is actually broken. The "reopen" transition and the
        # referenced states do not exist.
        if api.content.get_state(obj=question) == 'closed' and \
            api.content.get_state(obj=observation) == 'close-requested':
            api.content.transition(obj=observation, transition='reopen')
            api.content.transition(obj=question, transition='reopen')

        if api.content.get_state(observation) == 'phase2-draft':
            api.content.transition(obj=observation, transition='phase2-open')

        if api.content.get_state(observation).startswith('phase1-'):
            context.manage_addProperty('creator_role', 'Sector Expert',
                                       'string')
        else:
            context.manage_addProperty('creator_role', 'Review Expert',
                                       'string')
