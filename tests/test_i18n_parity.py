from __future__ import annotations

from exam_review_skill.i18n.locales import SUPPORTED_LOCALES, get_catalog, t
from exam_review_skill.i18n.output_modes import OutputMode, render_bilingual


def test_catalog_key_parity_zh_en():
    """Every catalog key must exist in BOTH zh-CN and en-US - no version with
    more features than the other."""
    zh = get_catalog("zh-CN")
    en = get_catalog("en-US")
    zh_only = set(zh) - set(en)
    en_only = set(en) - set(zh)
    assert zh_only == set(), f"zh-only keys: {sorted(zh_only)}"
    assert en_only == set(), f"en-only keys: {sorted(en_only)}"
    assert len(zh) == len(en)


def test_zh_and_en_same_keys_count():
    zh = get_catalog("zh-CN")
    en = get_catalog("en-US")
    assert len(zh) == len(en) >= 100


def test_output_mode_parse():
    assert OutputMode.parse("chinese") == OutputMode.CHINESE
    assert OutputMode.parse("zh-CN") == OutputMode.CHINESE
    assert OutputMode.parse("english") == OutputMode.ENGLISH
    assert OutputMode.parse("en-US") == OutputMode.ENGLISH
    assert OutputMode.parse("bilingual") == OutputMode.BILINGUAL
    assert OutputMode.parse(None) == OutputMode.BILINGUAL
    try:
        OutputMode.parse("french")
        assert False, "should raise"
    except ValueError:
        pass


def test_render_bilingual_chinese_main_english_term():
    zh = "贝叶斯公式用于条件概率计算"
    en = "Bayes' theorem"
    out = render_bilingual(zh=zh, en=en, mode="bilingual", primary="zh")
    # Chinese main text + English key term, NOT duplicated sentences
    assert "贝叶斯公式" in out
    assert "Bayes" in out
    assert out == "贝叶斯公式用于条件概率计算（Bayes' theorem）"


def test_render_bilingual_does_not_duplicate_long_sentences():
    """A long English sentence must NOT be appended (no full duplication)."""
    zh = "贝叶斯公式用于条件概率计算，是概率论的重要定理"
    en = "Bayes' theorem is used for conditional probability calculations and is an important theorem in probability theory"
    out = render_bilingual(zh=zh, en=en, mode="bilingual", primary="zh")
    assert out == zh  # main text only, English too long to be a term


def test_render_bilingual_english_main():
    out = render_bilingual(
        zh="中心极限定理", en="Central Limit Theorem", mode="bilingual", primary="en"
    )
    assert "Central Limit Theorem" in out
    assert "中心极限定理" in out


def test_render_single_language():
    assert render_bilingual(zh="中文", en="English", mode="chinese") == "中文"
    assert render_bilingual(zh="中文", en="English", mode="english") == "English"


def test_render_bilingual_with_terminology_map():
    from exam_review_skill.i18n import TerminologyMap

    tm = TerminologyMap(course_id="p")
    tm.add("central_limit_theorem", zh="中心极限定理", en="Central Limit Theorem")
    out = render_bilingual(
        zh="中心极限定理",
        en="Central Limit Theorem",
        mode="bilingual",
        term_map=tm,
        term_key="central_limit_theorem",
        primary="zh",
    )
    assert "中心极限定理" in out
    assert "Central Limit Theorem" in out


def test_mistake_and_diagnosis_localized():
    """User-facing mistake/diagnosis strings must be localizable in both locales."""
    assert t("zh-CN", "mistake.unit_error") == "单位错误"
    assert t("en-US", "mistake.unit_error") == "unit error"
    assert t("zh-CN", "diag.explain.prerequisite_gap") != t("en-US", "diag.explain.prerequisite_gap")
    assert t("zh-CN", "formula.ambiguity.fraction") != t("en-US", "formula.ambiguity.fraction")


def test_all_supported_locales_have_identical_keys():
    catalogs = {loc: set(get_catalog(loc)) for loc in SUPPORTED_LOCALES}
    reference = catalogs[SUPPORTED_LOCALES[0]]
    for locale, keys in catalogs.items():
        assert keys == reference, f"{locale} keys differ"
