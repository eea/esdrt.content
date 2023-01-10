import string

from Products.CMFCore.interfaces._content import IContentish
from zope.globalrequest import getRequest


def reduce_text(text, limit):
    if len(text) <= limit:
        return text
    new_text = text[:limit]
    new_text_split = new_text.split(' ')
    slice_size = -1 if len(new_text_split) > 1 else 1
    clean_text = ' '.join(new_text_split[:slice_size])

    if clean_text[-1] in string.punctuation:
        clean_text = clean_text[:-1]

    if isinstance(clean_text, unicode):
        return u'{0}...'.format(clean_text)
    else:
        return u'{0}...'.format(clean_text.decode('utf-8'))


def format_date(date, fmt='%d %b %Y, %H:%M CET'):
    return date.strftime(fmt)


def request_context(context):
    if context and IContentish.providedBy(context):
        return context

    req = getRequest()
    published = req.PUBLISHED

    # https://community.plone.org/t/context-aware-invariant-on-z3c-form-dx-add-form/13234/8
    try:
        container = published.context
    except AttributeError:
        container = published

    if IContentish.providedBy(container):
        return container

