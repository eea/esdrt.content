import json

from pathlib import Path
from copy import deepcopy
from zope.interface import Interface
from zope import schema
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from esdrt.content import _
from logging import getLogger
from collections import OrderedDict
logger = getLogger('esdrt.content.crf_codes')

DEFAULT_CRF_CODE_MAPPING = None

with open(Path(__file__).parent / "default_crf_code_mapping.json", "r") as default_crf_codes_file:
    DEFAULT_CRF_CODE_MAPPING = json.load(default_crf_codes_file)


def crf_codes(context=None):
    result = None

    if context:
        data = context.crf_code_mapping

    if not data:
        data = deepcopy(DEFAULT_CRF_CODE_MAPPING)

    if data:
        result = OrderedDict({x["code"]: x for x in data})

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
