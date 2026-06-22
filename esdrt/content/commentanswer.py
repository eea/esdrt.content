from AccessControl import getSecurityManager
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from Acquisition.interfaces import IAcquirer
from Products.Five import BrowserView
from plone.dexterity.browser import add
from plone.dexterity.browser import edit
from plone.dexterity.content import Container
from zope.interface import implementer

from esdrt.content import _
from plone import api
from plone.dexterity.interfaces import IDexterityFTI
from plone.supermodel import model
from plone.namedfile.interfaces import IImageScaleTraversable
from time import time
from z3c.form import field
from zope.component import createObject
from zope.component import getUtility
from zope import schema

# Interface class; used to define content-type schema.
class ICommentAnswer(model.Schema, IImageScaleTraversable):
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


@implementer(ICommentAnswer)
class CommentAnswer(Container):

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


class CommentAnswerView(BrowserView):

    def render(self):
        context = aq_inner(self.context)
        parent = aq_parent(context)
        url = '%s#%s' % (parent.absolute_url(), context.getId())

        return self.request.response.redirect(url)


class AddForm(add.DefaultAddForm):

    label = 'Answer'
    description = ''

    def updateFields(self):
        super(AddForm, self).updateFields()
        self.fields = field.Fields(ICommentAnswer).select('text')
        self.groups = [g for g in self.groups if g.label == 'label_schema_default']

    def updateWidgets(self):
        super(AddForm, self).updateWidgets()
        self.widgets['text'].rows = 15

    def create(self, data=None):
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


class AddView(add.DefaultAddView):
    form_instance: AddForm
    form = AddForm


class EditForm(edit.DefaultEditForm):

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
