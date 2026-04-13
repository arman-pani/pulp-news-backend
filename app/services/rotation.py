from __future__ import annotations

import logging

from app.core.redis_client import get_redis
from app.services.scraping_config import LANGUAGE_CYCLE, LANGUAGE_SOURCES

logger = logging.getLogger(__name__)

_TURN_KEY = "scraper:turn"
_IDX_KEY = "scraper:idx:{language}"


def get_current_turn() -> str:
    """Return the language scheduled for the next cron tick.

    Defaults to ``"english"`` when the key is absent (i.e. first run ever).
    """
    r = get_redis()
    return r.get(_TURN_KEY) or "english"


def get_and_advance_sources(language: str, count: int = 2) -> list[dict]:
    """Atomically increment the source index for *language* by *count* and return
    a list of source config dicts that should be scraped this run.

    Redis ``INCRBY`` initialises a missing key to 0 before incrementing.
    We return *count* sources, wrapping around modulo the total count per language to
    ensure continuous rotation across any list length (odd or even).
    """
    r = get_redis()
    key = _IDX_KEY.format(language=language)
    new_value = r.incrby(key, count)
    start_idx = new_value - count
    
    source_configs = LANGUAGE_SOURCES[language]
    sources = list(source_configs.values())
    num_sources = len(sources)
    
    selected = []
    for i in range(count):
        idx = (start_idx + i) % num_sources
        source = sources[idx]
        selected.append(source)
    
    source_names = ", ".join(s["source_name"] for s in selected)
    logger.info(
        "Rotation — language=%s sources=[%s] (start_idx=%d)",
        language,
        source_names,
        start_idx,
    )
    return selected


def advance_turn(current: str) -> str:
    """Move ``scraper:turn`` to the next language in *LANGUAGE_CYCLE*.

    Returns the new language value.
    """
    r = get_redis()
    pos = LANGUAGE_CYCLE.index(current)
    next_lang = LANGUAGE_CYCLE[(pos + 1) % len(LANGUAGE_CYCLE)]
    r.set(_TURN_KEY, next_lang)
    logger.debug("Turn advanced: %s → %s", current, next_lang)
    return next_lang
