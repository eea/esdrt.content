import os
import logging

from zope.component import getMultiAdapter

from Products.CMFCore.interfaces import IContentish
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.discussion.interfaces import IConversation
from plone.uuid.interfaces import IUUID

from collective.exportimport import export_other

from plone.restapi.interfaces import ISerializeToJson
import plone.api as api


logger = logging.getLogger(__name__)


class ExportDiscussion(export_other.ExportDiscussion):

    index = ViewPageTemplateFile(
        "templates/export_other.pt",
        _prefix=os.path.dirname(export_other.__file__),
    )


    def all_discussions(self):
        results = []
        for brain in api.content.find(
            object_provides=IContentish.__identifier__,
            sort_on="path",
            context=self.context,
        ):
            try:
                obj = brain.getObject()
                if obj is None:
                    logger.error(u"brain.getObject() is None %s", brain.getPath())
                    continue
                conversation = IConversation(obj, None)
                if not conversation:
                    continue
                serializer = getMultiAdapter(
                    (conversation, self.request), ISerializeToJson
                )
                output = serializer()
                if output:
                    results.append({
                        "@id": obj.absolute_url(),
                        "uuid": IUUID(obj),
                        "conversation": output
                    })
            except Exception:
                logger.info(
                    "Error exporting comments for %s", brain.getURL(), exc_info=True
                )
                continue
        return results

