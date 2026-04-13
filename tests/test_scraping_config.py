"""Tests for app.services.scraping_config source structure."""
from __future__ import annotations

import pytest

from app.services.scraping_config import LANGUAGE_CYCLE, LANGUAGE_SOURCES, MAX_ARTICLES_PER_SOURCE


# ---------------------------------------------------------------------------
# Top-level structure
# ---------------------------------------------------------------------------

def test_language_cycle_contains_three_languages():
    assert LANGUAGE_CYCLE == ["english", "odia", "bengali"]


def test_language_sources_has_all_cycle_keys():
    for lang in LANGUAGE_CYCLE:
        assert lang in LANGUAGE_SOURCES, f"Missing language key: {lang}"


def test_max_articles_per_source_is_positive():
    assert MAX_ARTICLES_PER_SOURCE > 0


# ---------------------------------------------------------------------------
# English sources
# ---------------------------------------------------------------------------

EXPECTED_ENGLISH = {
    "timesofindia", "thehindu", "hindustantimes", "ndtv_english",
    "news18_english", "deccanherald", "indianexpress", "indiatoday",
}

def test_english_sources_contain_expected_outlets():
    assert set(LANGUAGE_SOURCES["english"].keys()) == EXPECTED_ENGLISH


# ---------------------------------------------------------------------------
# Odia sources
# ---------------------------------------------------------------------------

EXPECTED_ODIA = {
    "sambad_odia", "prameya_odia", "khabarodisha", "odia_oneindia",
    "kanaknews", "dharitri", "thesamaja",
}

def test_odia_sources_contain_expected_outlets():
    assert set(LANGUAGE_SOURCES["odia"].keys()) == EXPECTED_ODIA


# ---------------------------------------------------------------------------
# Bengali sources
# ---------------------------------------------------------------------------

EXPECTED_BENGALI = {
    "zee_bengali", "abp_ananda", "sangbadpratidin", "news18_bengali",
    "eisamay", "tv9bangla", "uttarbangasambad",
}

def test_bengali_sources_contain_expected_outlets():
    assert set(LANGUAGE_SOURCES["bengali"].keys()) == EXPECTED_BENGALI


# ---------------------------------------------------------------------------
# Per-source schema validation
# ---------------------------------------------------------------------------

REQUIRED_KEYS = {"base_url", "rss_url", "source_name", "url_patterns"}

@pytest.mark.parametrize("language", LANGUAGE_CYCLE)
def test_every_source_has_required_keys(language):
    for source_key, config in LANGUAGE_SOURCES[language].items():
        missing = REQUIRED_KEYS - set(config.keys())
        assert not missing, f"{language}.{source_key} missing keys: {missing}"


@pytest.mark.parametrize("language", LANGUAGE_CYCLE)
def test_every_source_has_nonempty_source_name(language):
    for source_key, config in LANGUAGE_SOURCES[language].items():
        assert config["source_name"], f"{language}.{source_key} has empty source_name"


@pytest.mark.parametrize("language", LANGUAGE_CYCLE)
def test_every_source_has_nonempty_base_url(language):
    for source_key, config in LANGUAGE_SOURCES[language].items():
        assert config["base_url"], f"{language}.{source_key} has empty base_url"


@pytest.mark.parametrize("language", LANGUAGE_CYCLE)
def test_every_source_url_patterns_is_a_list(language):
    for source_key, config in LANGUAGE_SOURCES[language].items():
        assert isinstance(config["url_patterns"], list), (
            f"{language}.{source_key} url_patterns is not a list"
        )


# ---------------------------------------------------------------------------
# Source counts
# ---------------------------------------------------------------------------

def test_english_source_count():
    assert len(LANGUAGE_SOURCES["english"]) == 8


def test_odia_source_count():
    assert len(LANGUAGE_SOURCES["odia"]) == 7


def test_bengali_source_count():
    assert len(LANGUAGE_SOURCES["bengali"]) == 7
