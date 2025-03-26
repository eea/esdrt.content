"""plone.app.registry settings."""

import os

from zope.interface import Interface

from plone import schema

from esdrt.content import _

CSV_PATH = os.path.join(os.path.dirname(__file__), "data")


def read_profile_vocabulary(filename: str) -> str:
    """Read the contents of CSV_PATH/filename."""
    result = ""
    with open(os.path.join(CSV_PATH, filename), "r") as infile:
        result = infile.read().strip()
    return result


class IESDRTVocabularies(Interface):
    """Definition for Plone Registry."""

    eea_member_states = schema.Text(
        title=_("EEA Member States"),
        default=read_profile_vocabulary("eea_member_states.csv"),
    )

    ghg_source_category = schema.Text(
        title=_("NFR category group"),
        default=read_profile_vocabulary("ghg_source_category.csv"),
    )

    ghg_source_sectors = schema.Text(
        title=_("NFR Sector"),
        default=read_profile_vocabulary("ghg_source_sectors.csv"),
    )

    fuel = schema.Text(
        title=_("Fuel"),
        default=read_profile_vocabulary("fuel.csv"),
    )

    gas = schema.Text(
        title=_("Gas"),
        default=read_profile_vocabulary("gas.csv"),
    )

    highlight = schema.Text(
        title=_("Highlight"),
        default=read_profile_vocabulary("highlight.csv"),
    )

    parameter = schema.Text(
        title=_("Parameter"),
        default=read_profile_vocabulary("parameter.csv"),
    )

    conclusion_reasons = schema.Text(
        title=_("Conclusion Reasons"),
        default=read_profile_vocabulary("conclusion_reasons.csv"),
    )

    conclusion_phase2_reasons = schema.Text(
        title=_("Conclusion Phase2 Reasons"),
        default=read_profile_vocabulary("conclusion_phase2_reasons.csv"),
    )
