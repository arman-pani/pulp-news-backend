"""Tests for app.services.rotation — Redis-backed cron rotation state."""
from __future__ import annotations

import pytest

from app.services.scraping_config import LANGUAGE_CYCLE, LANGUAGE_SOURCES


# ---------------------------------------------------------------------------
# Helpers — fake Redis
# ---------------------------------------------------------------------------

class FakeRedis:
    """In-memory Redis stub that implements the subset used by rotation.py."""

    def __init__(self, initial: dict[str, str] | None = None):
        self._store: dict[str, str] = dict(initial or {})

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, value: str) -> None:
        self._store[key] = str(value)

    def incrby(self, key: str, amount: int) -> int:
        current = int(self._store.get(key, "0"))
        new_val = current + amount
        self._store[key] = str(new_val)
        return new_val


@pytest.fixture
def fake_redis(monkeypatch) -> FakeRedis:
    """Patch get_redis() in rotation module to return an in-memory store."""
    import app.services.rotation as rotation_module

    r = FakeRedis()
    monkeypatch.setattr(rotation_module, "get_redis", lambda: r)
    return r


# ---------------------------------------------------------------------------
# get_current_turn()
# ---------------------------------------------------------------------------

def test_get_current_turn_defaults_to_english_on_first_run(fake_redis):
    from app.services.rotation import get_current_turn

    assert get_current_turn() == "english"


def test_get_current_turn_returns_stored_value(fake_redis):
    from app.services.rotation import get_current_turn

    fake_redis.set("scraper:turn", "odia")
    assert get_current_turn() == "odia"


# ---------------------------------------------------------------------------
# get_and_advance_sources()
# ---------------------------------------------------------------------------

def test_get_and_advance_sources_first_call_returns_two_sources(fake_redis):
    from app.services.rotation import get_and_advance_sources

    sources = get_and_advance_sources("english", count=2)
    english_sources = list(LANGUAGE_SOURCES["english"].values())
    assert len(sources) == 2
    assert sources[0]["source_name"] == english_sources[0]["source_name"]
    assert sources[1]["source_name"] == english_sources[1]["source_name"]


def test_get_and_advance_sources_increments_index_by_count(fake_redis):
    from app.services.rotation import get_and_advance_sources

    # Call 1: idx 0, 1 -> next start_idx is 2
    get_and_advance_sources("english", count=2)
    # Call 2: idx 2, 3
    sources = get_and_advance_sources("english", count=2)
    
    english_sources = list(LANGUAGE_SOURCES["english"].values())
    assert sources[0]["source_name"] == english_sources[2]["source_name"]
    assert sources[1]["source_name"] == english_sources[3]["source_name"]


def test_get_and_advance_sources_wraps_around_perfectly(fake_redis):
    from app.services.rotation import get_and_advance_sources

    english_sources = list(LANGUAGE_SOURCES["english"].values())
    total = len(english_sources)
    # If total is 4, calling twice with count=2 uses [0,1] then [2,3]
    # Next call should be [0,1] again.
    
    iters = total // 2
    for _ in range(iters):
        get_and_advance_sources("english", count=2)

    wrapped = get_and_advance_sources("english", count=2)
    assert wrapped[0]["source_name"] == english_sources[0]["source_name"]


def test_get_and_advance_sources_handles_odd_list_length(fake_redis, monkeypatch):
    """Verify that we correctly wrap around when count=2 and mod is odd."""
    from app.services.rotation import get_and_advance_sources
    import app.services.rotation as rot
    
    # Mock LANGUAGE_SOURCES specifically for this test
    test_sources = {
        "odd_lang": {
            "s1": {"source_name": "A"},
            "s2": {"source_name": "B"},
            "s3": {"source_name": "C"},
        }
    }
    monkeypatch.setattr(rot, "LANGUAGE_SOURCES", test_sources)
    
    # Run 1: [A, B] (idx 0, 1) -> next 2
    r1 = get_and_advance_sources("odd_lang", count=2)
    assert [s["source_name"] for s in r1] == ["A", "B"]
    
    # Run 2: [C, A] (idx 2, 3%3=0) -> next 4
    r2 = get_and_advance_sources("odd_lang", count=2)
    assert [s["source_name"] for s in r2] == ["C", "A"]
    
    # Run 3: [B, C] (idx 4%3=1, 5%3=2) -> next 6
    r3 = get_and_advance_sources("odd_lang", count=2)
    assert [s["source_name"] for s in r3] == ["B", "C"]
    
    # Run 4: [A, B] (idx 6%3=0, 7%3=1)
    r4 = get_and_advance_sources("odd_lang", count=2)
    assert [s["source_name"] for s in r4] == ["A", "B"]


def test_get_and_advance_sources_independent_per_language(fake_redis):
    """Odia and English indices are tracked separately."""
    from app.services.rotation import get_and_advance_sources

    en0 = get_and_advance_sources("english", count=2)
    od0 = get_and_advance_sources("odia", count=2)

    english_sources = list(LANGUAGE_SOURCES["english"].values())
    odia_sources = list(LANGUAGE_SOURCES["odia"].values())

    assert [s["source_name"] for s in en0] == [english_sources[0]["source_name"], english_sources[1]["source_name"]]
    assert [s["source_name"] for s in od0] == [odia_sources[0]["source_name"], odia_sources[1]["source_name"]]


# ---------------------------------------------------------------------------
# advance_turn()
# ---------------------------------------------------------------------------

def test_advance_turn_cycles_english_to_odia(fake_redis):
    from app.services.rotation import advance_turn

    assert advance_turn("english") == "odia"
    assert fake_redis.get("scraper:turn") == "odia"


def test_advance_turn_cycles_odia_to_bengali(fake_redis):
    from app.services.rotation import advance_turn

    assert advance_turn("odia") == "bengali"


def test_advance_turn_cycles_bengali_back_to_english(fake_redis):
    from app.services.rotation import advance_turn

    assert advance_turn("bengali") == "english"


def test_advance_turn_full_cycle(fake_redis):
    from app.services.rotation import advance_turn, get_current_turn

    fake_redis.set("scraper:turn", "english")
    for expected in ["odia", "bengali", "english"]:
        current = get_current_turn()
        assert advance_turn(current) == expected


# ---------------------------------------------------------------------------
# Full rotation simulation — three consecutive ticks
# ---------------------------------------------------------------------------

def test_three_tick_rotation_covers_all_languages(fake_redis):
    """Simulates exactly what the cron job does on three consecutive runs."""
    from app.services.rotation import advance_turn, get_and_advance_sources, get_current_turn

    seen_languages = []
    for _ in range(3):
        lang = get_current_turn()
        get_and_advance_sources(lang, count=2)
        advance_turn(lang)
        seen_languages.append(lang)

    assert seen_languages == ["english", "odia", "bengali"]
