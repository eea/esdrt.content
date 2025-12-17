from Products.Five.browser import BrowserView

import plone.api as api

from esdrt.content.browser.carryover import catalog_with_children


class ReindexContext(BrowserView):
    def __call__(self):
        catalog = api.portal.get_tool("portal_catalog")
        catalog_with_children(catalog, self.context)
        return self.request.RESPONSE.redirect(self.context.absolute_url())
