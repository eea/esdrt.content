import uuid
import logging

from urllib.parse import unquote
from urllib.parse import urlparse

from collective.exportimport.import_content import ImportContent

import plone.api as api


logger = logging.getLogger(__name__)


SIMPLE_SETTER_FIELDS = {
    # "ALL": ["some_shared_field"],
    "ReviewFolder": [
        "tableau_statistics_roles",
    ],
    "Conclusion": [
      "ghg_estimations",
      "closing_reason",
    ],
    "ConclusionsPhase2": [
      "ghg_estimations",
      "closing_reason",
    ],
    "Observation": [
        "country",
        "crf_code",
        "year",
        "pollutants",
        "scenario",
        "fuel",
        "gas",
        "parameter",
        "highlight",
    ],
}


class CustomImportContent(ImportContent):

    SEEN_UIDS = None

    def start(self):
        self.SEEN_UIDS = set()

    def global_dict_hook(self, item):
        simple = {}
        # for fieldname in SIMPLE_SETTER_FIELDS.get("ALL", []):
        #     if fieldname in item:
        #         value = item.pop(fieldname)
        #         if value:
        #             simple[fieldname] = value
        if not item["title"]:
            item["title"] = item["id"]

        if item["@type"] == "Observation":
            # fix integer years
            if isinstance(item.get("year"), int):
                item["year"] = str(item["year"])

        if item.get("UID") in self.SEEN_UIDS:
            item["UID"] = uuid.uuid4().hex
            logger.info(
                "Duplicate UID detected, new UID generated: %s: %s",
                item["@id"], item["UID"]
            )

        self.SEEN_UIDS.add(item.get("UID"))

        for fieldname in SIMPLE_SETTER_FIELDS.get(item["@type"], []):
            if fieldname in item:
                value = item.pop(fieldname)
                if value:
                    simple[fieldname] = value
        if simple:
            item["exportimport.simplesetter"] = simple

        return item

    def get_parent_as_container(self, item):
        """Get parent by path, not by UID, there were issues with duplicate UIDs in import data."""
        parent_url = unquote(item["parent"]["@id"])
        parent_path = urlparse(parent_url).path
        return api.content.get(path=parent_path)

    def global_obj_hook_before_deserializing(self, obj, item):
        to_set = item.get("exportimport.simplesetter", {}).items()

        for fieldname, value in to_set:
            setattr(obj, fieldname, value)

        return obj, item
