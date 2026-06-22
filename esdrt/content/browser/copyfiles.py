from Acquisition import aq_inner
from Acquisition import aq_parent
from Products.Five import BrowserView


class CopyFileToAnswer(BrowserView):

    def render(self):
        context = aq_inner(self.context)
        conversation = aq_parent(context)
        answer = aq_parent(conversation)
        file = getattr(context, 'attachment', None)
        candidate_id = file.filename
        while candidate_id in list(answer.keys()):
            candidate_id += '-1'

        filename = answer.invokeFactory(
            id=candidate_id,
            type_name='ESDRTFile',
            file=file,
        )
        return self.request.response.redirect(context.absolute_url())
