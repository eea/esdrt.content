import logging

from Products.CMFCore.utils import getToolByName

from esdrt.content.upgrades import portal_workflow as upw

LOG = logging.getLogger(__name__)


def upgrade(context):
    catalog = getToolByName(context, "portal_catalog")
    objects = [b.getObject() for b in catalog(portal_type=["Observation"])]
    len_objects = len(objects)
    for idx, obs in enumerate(objects, start=1):
        if idx % 100 == 0:
            LOG.info("Done: %s/%s", idx, len_objects)

        catalog.reindexObject(
            obs, update_metadata=True,
        )
