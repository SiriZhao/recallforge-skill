from __future__ import annotations

import pytest

from exam_review_skill.i18n import LanguageProfile
from exam_review_skill.i18n.locales import (
    SUPPORTED_LOCALES,
    get_catalog,
    register_locale,
    t,
)


def test_supported_locales():
    assert "zh-CN" in SUPPORTED_LOCALES
    assert "en-US" in SUPPORTED_LOCALES


def test_locale_switch_same_key_different_output():
    zh = t("zh-CN", "plan.block.why", why="x")
    en = t("en-US", "plan.block.why", why="x")
    assert zh != en
    assert "为什么" in zh
    assert "Why" in en


def test_missing_key_fails_closed():
    assert t("zh-CN", "no.such.key") == "no.such.key"
    assert t("en-US", "no.such.key") == "no.such.key"


def test_formatting_errors_do_not_crash():
    # missing format arg falls back to the raw template, never raises
    assert isinstance(t("zh-CN", "plan.block.why"), str)


def test_language_level_fallback():
    # zh-TW falls back to the zh catalog without registering it explicitly
    zh_tw = t("zh-TW", "plan.block.why", why="x")
    assert "为什么" in zh_tw


def test_register_new_locale_is_extensible():
    register_locale("ja-JP", {"plan.block.why": "理由：{why}"})
    assert "plan.block.why" in get_catalog("ja-JP")
    assert t("ja-JP", "plan.block.why", why="x") == "理由：x"
    # unknown keys still fail closed in the new locale
    assert t("ja-JP", "no.such.key") == "no.such.key"


def test_language_profile_validation():
    assert LanguageProfile().validate() == []
    assert LanguageProfile(ui_locale="fr-FR").validate() != []  # unsupported
    assert LanguageProfile(output_language="de-DE").validate() != []
    assert LanguageProfile(terminology_mode="side-by-side").validate() != []


def test_unknown_locale_falls_back_to_en():
    assert t("xx-XX", "plan.title", date="2026-06-18", hours="6") == "Global daily plan 2026-06-18 (6 hours total)"
