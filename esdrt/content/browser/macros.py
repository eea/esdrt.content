from Products.Five.browser import BrowserView

from esdrt.content.utils import reduce_text
from esdrt.content.utils import format_date


class MacrosView(BrowserView):

    @staticmethod
    def reduce_text(text, limit=500):
        return reduce_text(text, limit)

    @staticmethod
    def format_date(date):
        return format_date(date)
