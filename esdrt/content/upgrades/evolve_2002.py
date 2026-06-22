from logging import getLogger

from esdrt.content.upgrades.reindex_observations import reindex_observations


def upgrade(_, logger=None):
    if logger is None:
        logger = getLogger("esdrt.content.upgrades.2002")

    reindex_observations(logger, ("parameter", "qa_extract", "phase_timestamp"))
