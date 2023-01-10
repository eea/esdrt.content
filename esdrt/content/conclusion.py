from copy import copy
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

from esdrt.content.utils import exclude_phase2_actions


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

    remarks = schema.Text(
        title=_(u'Concluding remark'),
        description=_(u'(visible to MS when observation finalised)'),
        required=False,
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
        menu_items = exclude_phase2_actions(parent, menu_items)
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
        conclusion_fields = field.Fields(IConclusion).select(
            'closing_reason', 'text', 'remarks')
        observation_fields = field.Fields(IObservation).select('highlight')
        self.fields = field.Fields(conclusion_fields, observation_fields)
        self.fields['highlight'].widgetFactory = CheckBoxFieldWidget
        self.groups = [
            g for g in self.groups if g.label == 'label_schema_default']

    def updateWidgets(self):
        super(AddForm, self).updateWidgets()
        self.widgets['text'].rows = 15
        self.widgets['remarks'].rows = 15

    def update(self):
        super(AddForm, self).update()

        if not self.context.enable_steps:
            self.label = "Conclusions"

        # grab highlight value from observation
        widget_highlight = self.widgets['highlight']
        context_highlight = self.context.highlight or []

        if isinstance(type(widget_highlight).items, property):
            # newer z3c.form
            def is_checked(term):
                return term.value in context_highlight

            # Monkey patch isChecked method since we can't
            # override .items anymore. It's now a @property.
            widget_highlight.isChecked = is_checked
        else:
            # older z3c.form
            def set_checked(item):
                updated_item = copy(item)
                updated_item['checked'] = (
                    updated_item['value'] in (self.context.highlight or [])
                )
                return updated_item
        widget_highlight.items = map(set_checked, widget_highlight.items)

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
        content.remarks = self.request.form.get('form.widgets.remarks', '')
        reason = self.request.form.get('form.widgets.closing_reason')
        content.closing_reason = reason[0]
        adapted = IAllowDiscussion(content)
        adapted.allow_discussion = True

        # Edit highlighs
        highlight = self.request.form.get('form.widgets.highlight')
        container.highlight = highlight
        notify(ObjectModifiedEvent(container))

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
        data['remarks'] = context.remarks
        if type(context.closing_reason) in (ListType, TupleType):
            data['closing_reason'] = context.closing_reason[0]
        else:
            data['closing_reason'] = context.closing_reason
        data['highlight'] = container.highlight
        return data

    def update(self):
        super(EditForm, self).update()

        if not self.context.enable_steps:
            self.label = "Conclusions"

    def updateFields(self):
        super(EditForm, self).updateFields()
        from .observation import IObservation
        conclusion_fields = field.Fields(IConclusion).select(
            'closing_reason', 'text', 'remarks')
        observation_fields = field.Fields(IObservation).select('highlight')
        self.fields = field.Fields(conclusion_fields, observation_fields)
        self.fields['highlight'].widgetFactory = CheckBoxFieldWidget
        self.groups = [g for g in self.groups if g.label == 'label_schema_default']

    def updateWidgets(self):
        super(EditForm, self).updateWidgets()
        self.widgets['text'].rows = 15
        self.widgets['remarks'].rows = 15

    def updateActions(self):
        super(EditForm, self).updateActions()
        for k in self.actions.keys():
            self.actions[k].addClass('standardButton')

    def applyChanges(self, data):
        super(EditForm, self).applyChanges(data)
        context = aq_inner(self.context)
        container = aq_parent(context)
        text = self.request.form.get('form.widgets.text')
        remarks = self.request.form.get('form.widgets.remarks')
        closing_reason = self.request.form.get('form.widgets.closing_reason')
        context.text = text
        context.remarks = remarks
        if type(closing_reason) in (ListType, TupleType):
            context.closing_reason = closing_reason[0]
        highlight = self.request.form.get('form.widgets.highlight')
        container.highlight = highlight
        notify(ObjectModifiedEvent(context))
        notify(ObjectModifiedEvent(container))
