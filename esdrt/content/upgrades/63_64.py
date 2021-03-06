from Products.CMFCore.utils import getToolByName

from esdrt.content.upgrades import portal_workflow as upw


def upgrade(context):
    catalog = getToolByName(context, 'portal_catalog')
    wft = getToolByName(context, 'portal_workflow')
    type_mapping = upw.get_workflow_type_mapping(wft)

    queries = [
        dict(
            portal_type='Observation',
            review_state=['phase2-pending', 'phase1-pending'],
            reindex_self_only=True,
        ),
    ]

    upw.upgrade(wft, catalog, type_mapping, queries)

