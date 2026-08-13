from __future__ import annotations

from recallforge.i18n import TerminologyMap


def test_add_and_localize():
    tm = TerminologyMap(course_id="chem101")
    tm.add("conditional_probability", zh="条件概率", en="conditional probability")
    assert tm.localize("conditional_probability", "zh-CN") == "条件概率"
    assert tm.localize("条件概率", "en-US") == "conditional probability"
    assert tm.localize("conditional probability", "zh-CN") == "条件概率"


def test_aliases_and_apostrophe_normalization():
    tm = TerminologyMap()
    tm.add("bayes_theorem", zh="贝叶斯公式", en="Bayes' theorem", aliases=["Bayes公式"])
    assert tm.canonical_key("Bayes' theorem") == "bayes_theorem"
    assert tm.canonical_key("Bayes theorem") == "bayes_theorem"  # apostrophe stripped
    assert tm.canonical_key("贝叶斯公式") == "bayes_theorem"
    assert tm.canonical_key("Bayes公式") == "bayes_theorem"


def test_state_round_trip():
    tm = TerminologyMap(course_id="prob")
    tm.add("random_variable", zh="随机变量", en="random variable", aliases=["RV"])
    state = tm.to_state()
    restored = TerminologyMap.from_state(state)
    assert restored.course_id == "prob"
    assert restored.canonical_key("随机变量") == "random_variable"
    assert restored.canonical_key("RV") == "random_variable"
    assert restored.localize("random_variable", "zh-CN") == "随机变量"


def test_unknown_term_returns_none():
    tm = TerminologyMap()
    assert tm.canonical_key("unknown thing") is None
    assert tm.localize("unknown thing", "zh-CN") is None
