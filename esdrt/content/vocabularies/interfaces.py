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
