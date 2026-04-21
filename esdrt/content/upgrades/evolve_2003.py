from logging import getLogger

from esdrt.content.upgrades.reindex_observations import reindex_observations


def upgrade(_, logger=None):
    if logger is None:
        logger = getLogger("esdrt.content.upgrades.2003")

    reindex_observations(logger, ["qa_extract"])
