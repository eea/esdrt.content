from zope.interface import Interface
from zope import schema
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from esdrt.content import MessageFactory as _
from logging import getLogger
from collections import OrderedDict
logger = getLogger('esdrt.content.crf_codes')

class IEsdrtSettings(Interface):
    """Settings expected to be found in plone.registry
    """

    crfcodeMapping = schema.Dict(
        title=_(u"CRF Codes"),
        description=_(u"Maps ldap sectors"),
        key_type=schema.TextLine(title=_(u"Code")),
        value_type=schema.TextLine(
            title=_(u"Sector Item"),
            description=_(u"Descripe a sector in the form: ldap|code|name|title")
        ),
    )


def crf_codes():
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

    for key, codes in crfcodeMapping.items():
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


def get_category_ldap_from_crf_code(value):
    """ get the CRF category this CRF Code matches
        According to the rules previously set
        for LDAP Matching
    """
    crfcodes = crf_codes()
    return crfcodes.get(value, {}).get('ldap', '')


def get_category_value_from_crf_code(value):
    """ get the CRF category value to show it in the observation metadata """
    crfcodes = crf_codes()
    # return crf_codes.get(value, {}).get('sectorname', '')
    return crfcodes.get(value, {}).get('title', '')
