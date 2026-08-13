from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
def test_trigger_cases_and_boundaries_are_documented():
    skill=(ROOT/"skill/recallforge/SKILL.md").read_text(encoding="utf-8").lower()
    cases=json.loads((ROOT/"tests/skill-trigger-cases/cases.json").read_text(encoding="utf-8"))
    for phrase in ("exam review", "active recall", "mock exam", "weak-topic", "code or pull-request review", "translation-only"):
        assert phrase in skill
    assert len(cases["should_trigger"]) >= 4 and len(cases["should_not_trigger"]) >= 4
def test_self_test_contract():
    skill=(ROOT/"skill/recallforge/SKILL.md").read_text(encoding="utf-8")
    for line in ("✓ Skill activated", "✓ Course material parsed", "✓ Knowledge structure created", "✓ Active-recall question generated", "✓ Exam-style practice generated", "Status: READY"):
        assert line in skill
    assert (ROOT/"skill/recallforge/assets/self-test/mini-course.md").is_file()
