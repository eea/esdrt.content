from copy import deepcopy
from logging import getLogger

from zope.component import getUtility

from plone.registry.interfaces import IRegistry

import plone.api as api

logger = getLogger(__name__)


def delete_registry_records():
    registry = getUtility(IRegistry)

    to_delete = [
        "esdrt.content.crf_code_matching.IEsdrtSettings",
        "esdrt.content.vocabularies.interfaces.IESDRTVocabularies",
    ]

    found = []
    for name in to_delete:
        for record in registry.records:
            if record.startswith(name):
                found.append(record)

    for name in found:
        logger.info("Removing %s from registry!", name)
        del registry.records[name]


def save_default_vocabulary_values():
    catalog = api.portal.get_tool("portal_catalog")

    query = {
        "portal_type": ["ReviewFolder"],
    }

    brains = catalog(**query)

    vocab_names = [
        "vocab_eea_member_states",
        "vocab_ghg_source_category",
        "vocab_ghg_source_sectors",
        "vocab_gas",
        "vocab_fuel",
        "vocab_highlight",
        "vocab_parameter",
        "vocab_conclusion_reasons",
        "vocab_conclusion_phase2_reasons",
    ]

    for brain in brains:
        folder = brain.getObject()
        for v_name in vocab_names:
            if v_name not in folder.__dict__:
                logger.info("Setting %s for %s", v_name, folder.absolute_url(1))
                default_value = getattr(folder, v_name)
                setattr(folder, v_name, default_value)


def upgrade(_):
    delete_registry_records()
    save_default_vocabulary_values()

