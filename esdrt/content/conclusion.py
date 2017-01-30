from AccessControl import getSecurityManager
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from Acquisition.interfaces import IAcquirer
from esdrt.content import MessageFactory as _
from five import grok
from plone import api
from plone.app.dexterity.behaviors.discussion import IAllowDiscussion
from plone.dexterity.interfaces import IDexterityFTI
from plone.directives import dexterity
from plone.directives import form
from plone.namedfile.interfaces import IImageScaleTraversable
from time import time
from z3c.form import field
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.browsermenu.menu import getMenu
from zope.component import createObject
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.schema.interfaces import IVocabularyFactory
from types import ListType
from types import TupleType
from zope.lifecycleevent import ObjectModifiedEvent
from zope.event import notify


class IConclusion(form.Schema, IImageScaleTraversable):
    """
    Conclusions of this observation
    """

    closing_reason = schema.Choice(
        title=_(u'Status of observation'),
        vocabulary='esdrt.content.conclusionreasons',
        required=True,

    )

    text = schema.Text(
        title=_(u'Internal note for expert/reviewers'),
        required=True,
        )





HIDDEN_ACTIONS = [
    '/content_status_history',
    '/placeful_workflow_configuration',
]


def hidden(menuitem):
    for action in HIDDEN_ACTIONS:
        if menuitem.get('action').endswith(action):
            return True
    return False


# Custom content-type class; objects created for this content type will
# be instances of this class. Use this class to add content-type specific
# methods and properties. Put methods that are mainly useful for rendering
# in separate view classes.
class Conclusion(dexterity.Container):
    grok.implements(IConclusion)
    # Add your class methods and properties here

    def reason_value(self):
        return self._vocabulary_value('esdrt.content.conclusionreasons',
            self.closing_reason
        )

    def _vocabulary_value(self, vocabulary, term):
        vocab_factory = getUtility(IVocabularyFactory, name=vocabulary)
        vocabulary = vocab_factory(self)
        if not term:
            return u''
        try:
            value = vocabulary.getTerm(term)
            return value.title
        except LookupError:
            return term

    def can_edit(self):
        sm = getSecurityManager()
        return sm.checkPermission('Modify portal content', self)

    def can_delete(self):
        sm = getSecurityManager()
        return sm.checkPermission('Delete objects', self)

    def can_add_files(self):
        sm = getSecurityManager()
        return sm.checkPermission('esdrt.content: Add ESDRTFile', self)

    def get_actions(self):
        parent = aq_parent(self)
        request = getRequest()
        question_menu_items = getMenu(
            'plone_contentmenu_workflow',
            self,
            request
            )
        observation_menu_items = getMenu(
            'plone_contentmenu_workflow',
            parent,
            request
            )
        menu_items = question_menu_items + observation_menu_items
        return [mitem for mitem in menu_items if not hidden(mitem)]

    def get_files(self):
        items = self.values()
        mtool = api.portal.get_tool('portal_membership')
        return [item for item in items if mtool.checkPermission('View', item)]

# View class
# The view will automatically use a similarly named template in
# templates called conclusionview.pt .
# Template filenames should be all lower case.
# The view will render when you request a content object with this
# interface with "/@@view" appended unless specified otherwise
# using grok.name below.
# This will make this view the default view for your content-type
grok.templatedir('templates')


class ConclusionView(grok.View):
    grok.context(IConclusion)
    grok.require('zope2.View')
    grok.name('view')

    def render(self):
        context = aq_inner(self.context)
        parent = aq_parent(context)
        url = '%s#tab-conclusions' % parent.absolute_url()

        return self.request.response.redirect(url)


class AddForm(dexterity.AddForm):
    grok.name('esdrt.content.conclusion')
    grok.context(IConclusion)
    grok.require('esdrt.content.AddConclusion')

    label = 'Conclusions Step 1'
    description = ''

    def updateFields(self):
        from .observation import IObservation
        super(AddForm, self).updateFields()
        conclusion_fields = field.Fields(IConclusion).select('closing_reason', 'text')
        observation_fields = field.Fields(IObservation).select('highlight')
        self.fields = field.Fields(conclusion_fields, observation_fields)
        self.fields['highlight'].widgetFactory = CheckBoxFieldWidget
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
        reason = self.request.form.get('form.widgets.closing_reason')
        content.closing_reason = reason[0]
        adapted = IAllowDiscussion(content)
        adapted.allow_discussion = True

        # Edit highlighs
        highlights = self.request.form.get('form.widgets.highlight')
        container.highlights = highlights

        # Update Observation state
        api.content.transition(
            obj=self.context,
            transition='phase1-draft-conclusions'
        )

        return aq_base(content)

    def updateActions(self):
        super(AddForm, self).updateActions()
        self.actions['save'].addClass('defaultWFButton')
        for k in self.actions.keys():
            self.actions[k].addClass('standardButton')


class EditForm(dexterity.EditForm):
    grok.name('edit')
    grok.context(IConclusion)
    grok.require('cmf.ModifyPortalContent')

    label = 'Conclusions Step 1'
    description = ''
    ignoreContext = False

    def getContent(self):
        context = aq_inner(self.context)
        container = aq_parent(context)
        data = {}
        data['text'] = context.text
        if type(context.closing_reason) in (ListType, TupleType):
            data['closing_reason'] = context.closing_reason[0]
        else:
            data['closing_reason'] = context.closing_reason
        data['highlight'] = container.highlight
        return data

    def updateFields(self):
        super(EditForm, self).updateFields()
        from .observation import IObservation
        conclusion_fields = field.Fields(IConclusion).select('closing_reason', 'text')
        observation_fields = field.Fields(IObservation).select('highlight')
        self.fields = field.Fields(conclusion_fields, observation_fields)
        self.fields['highlight'].widgetFactory = CheckBoxFieldWidget
        self.groups = [g for g in self.groups if g.label == 'label_schema_default']

    def updateWidgets(self):
        super(EditForm, self).updateWidgets()
        self.widgets['text'].rows = 15

    def updateActions(self):
        super(EditForm, self).updateActions()
        for k in self.actions.keys():
            self.actions[k].addClass('standardButton')

    def applyChanges(self, data):
        super(EditForm, self).applyChanges(data)
        context = aq_inner(self.context)
        container = aq_parent(context)
        text = self.request.form.get('form.widgets.text')
        closing_reason = self.request.form.get('form.widgets.closing_reason')
        context.text = text
        if type(closing_reason) in (ListType, TupleType):
            context.closing_reason = closing_reason[0]
        highlight = self.request.form.get('form.widgets.highlight')
        container.highlight = highlight
        notify(ObjectModifiedEvent(context))
        notify(ObjectModifiedEvent(container))
