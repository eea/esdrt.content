# -*- coding: utf-8 -*-
import os
import dateutil

from urllib.parse import unquote
from urllib.parse import urlparse
from html import unescape

from plone import api

import logging

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.discussion.interfaces import IConversation

from collective.exportimport import import_other

from collective.exportimport.import_other import LLSet
from collective.exportimport.import_other import Comment
from collective.exportimport.import_other import aq_base
from collective.exportimport.import_other import IAnnotations
from collective.exportimport.import_other import DISCUSSION_ANNOTATION_KEY


logger = logging.getLogger(__name__)


class ImportDiscussion(import_other.ImportDiscussion):
    """Import discussions / comments

    Custom import so that discussion parents are retrieved
    based on path instead of UID.
    """

    index = ViewPageTemplateFile(
        "templates/import_discussion.pt",
        _prefix=os.path.dirname(import_other.__file__),
    )

    def import_data(self, data):
        results = 0
        for conversation_data in data:
            parent_url = unquote(conversation_data["@id"])
            parent_path = urlparse(parent_url).path
            obj = api.content.get(path=parent_path)
            if not obj:
                continue
            added = 0
            conversation = IConversation(obj)

            for item in conversation_data["conversation"]["items"]:

                if isinstance(item["text"], dict) and item["text"].get("data"):
                    item["text"] = item["text"]["data"]

                comment = Comment()
                comment_id = int(item["comment_id"])
                comment.comment_id = comment_id
                comment.creation_date = dateutil.parser.parse(item["creation_date"])
                comment.modification_date = dateutil.parser.parse(
                    item["modification_date"]
                )
                comment.author_name = item["author_name"]
                comment.author_username = item["author_username"]
                comment.creator = item["author_username"]
                comment.text = unescape(
                    item["text"]
                    .replace(u"\r<br />", u"\r\n")
                    .replace(u"<br />", u"\r\n")
                )

                if item["user_notification"]:
                    comment.user_notification = True
                if item.get("in_reply_to"):
                    comment.in_reply_to = int(item["in_reply_to"])

                conversation._comments[comment_id] = comment
                comment.__parent__ = aq_base(conversation)
                commentator = comment.author_username
                if commentator:
                    if commentator not in conversation._commentators:
                        conversation._commentators[commentator] = 0
                    conversation._commentators[commentator] += 1

                reply_to = comment.in_reply_to
                if not reply_to:
                    # top level comments are in reply to the faux id 0
                    comment.in_reply_to = reply_to = 0

                if reply_to not in conversation._children:
                    conversation._children[reply_to] = LLSet()
                conversation._children[reply_to].insert(comment_id)

                # Add the annotation if not already done
                annotions = IAnnotations(obj)
                if DISCUSSION_ANNOTATION_KEY not in annotions:
                    annotions[DISCUSSION_ANNOTATION_KEY] = aq_base(conversation)
                added += 1
            logger.info("Added {} comments to {}".format(added, obj.absolute_url()))
            results += added

        return results
