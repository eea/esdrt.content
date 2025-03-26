from plone.app.discussion.browser.comments import CommentForm as BaseForm
from plone.app.discussion.browser.comments import CommentsViewlet as BaseViewlet


class CommentForm(BaseForm):

    def updateWidgets(self):
        super(CommentForm, self).updateWidgets()
        self.widgets['text'].rows = 15

    def updateActions(self):
        super(CommentForm, self).updateActions()
        self.actions['comment'].title = 'Save Comment'
        for k in list(self.actions.keys()):
            self.actions[k].addClass('standardButton')
            self.actions[k].addClass('defaultWFButton')


class CommentsViewlet(BaseViewlet):
    form = CommentForm
