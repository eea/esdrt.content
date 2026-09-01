from zope.interface import Interface
from zope import schema
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from esdrt.content import _
from logging import getLogger
from collections import OrderedDict
logger = getLogger('esdrt.content.crf_codes')

class IEsdrtSettings(Interface):
    """Settings expected to be found in plone.registry
    """

    crfcodeMapping = schema.Dict(
        title=_("CRF Codes"),
        description=_("Maps ldap sectors"),
        key_type=schema.TextLine(title=_("Code")),
        value_type=schema.TextLine(
            title=_("Sector Item"),
            description=_("Descripe a sector in the form: ldap|code|name|title")
        ),
    )


def crf_codes_from_registry():
    """ get the CRF code mapping from portal_registry
        @retrun a dictionary
        {
            "key": {
                "ldap": "sector",
                "code": "key",
                "name": "name",
                "title": "title"
            },
            ...
        }
    """
    registry = getUtility(IRegistry)
    crfcodeMapping = registry.forInterface(IEsdrtSettings).crfcodeMapping

    crf_codes = {}

    for key, codes in list(crfcodeMapping.items()):
        try:
            ldap, code, name, title = codes.split('|')
            crf_codes[key] = {
                "ldap": ldap,
                "code": code,
                "name": name,
                "title": title
            }
        except:
            logger.warning('%s is not well formatted' % key)

    return OrderedDict(sorted(crf_codes.items()))


def crf_codes_from_context(context):
    result = None

    data = context.crf_code_mapping

    if data:
        result = OrderedDict({x["code"]: x for x in data})

    return result


def crf_codes(context=None):
    result = None

    if context:
        result = crf_codes_from_context(context)

    if not result:
        result = crf_codes_from_registry()

    return result


def get_category_ldap_from_crf_code(value, context=None):
    """ get the CRF category this CRF Code matches
        According to the rules previously set
        for LDAP Matching
    """
    crfcodes = crf_codes(context)
    return crfcodes.get(value, {}).get('ldap', '')


def get_category_value_from_crf_code(value, context=None):
    """ get the CRF category value to show it in the observation metadata """
    crfcodes = crf_codes(context)
    return crfcodes.get(value, {}).get('title', '')
