from __future__ import annotations

import re


def _normalize(text: str) -> str:
    """Canonical token form: lowercase, collapse whitespace, strip apostrophes and
    edge punctuation. Used to match 'Bayes' theorem' / '贝叶斯公式' / 'Bayes公式'
    to one canonical topic key via the terminology map."""
    s = str(text or "").strip().lower()
    s = s.replace("'", "").replace("’", "")
    s = re.sub(r"[\s\u3000]+", " ", s)
    s = s.strip(" '\"“”‘’`()[]{}.,;:!?。，；：！？·")
    return s


class TerminologyMap:
    """Per-course Chinese/English terminology map.

    Structure (stable English keys):
        { "conditional probability": { "names": {"zh-CN": "条件概率", "en-US": "conditional probability"},
                                        "aliases": ["条件概率", "conditional probability"] } }

    A reverse index maps every name/alias (normalized) to its canonical key, so mixed
    language materials resolve to the same topic without re-translating each time.
    """

    def __init__(self, course_id: str = ""):
        self.course_id = course_id
        self._terms: dict[str, dict] = {}
        self._index: dict[str, str] = {}

    @property
    def terms(self) -> dict[str, dict]:
        return self._terms

    def add(
        self,
        key: str,
        *,
        zh: str | None = None,
        en: str | None = None,
        names: dict[str, str] | None = None,
        aliases: list[str] | None = None,
    ) -> None:
        key = _normalize(key) or key
        entry = self._terms.setdefault(key, {"names": {}, "aliases": []})
        if names:
            entry["names"].update({k: v for k, v in names.items()})
        if zh:
            entry["names"]["zh-CN"] = zh
        if en:
            entry["names"]["en-US"] = en
        for alias in aliases or []:
            if alias not in entry["aliases"]:
                entry["aliases"].append(alias)
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        self._index = {}
        for key, entry in self._terms.items():
            tokens = [key]
            tokens.extend(entry.get("names", {}).values())
            tokens.extend(entry.get("aliases", []))
            for token in tokens:
                norm = _normalize(token)
                if norm:
                    self._index.setdefault(norm, key)

    def canonical_key(self, term: str) -> str | None:
        return self._index.get(_normalize(term))

    def localize(self, key_or_term: str, locale: str) -> str | None:
        key = self.canonical_key(key_or_term) or key_or_term
        entry = self._terms.get(key)
        if not entry:
            return None
        names = entry.get("names", {})
        return names.get(locale) or names.get("en-US")

    def resolve_topic(self, text: str) -> tuple[str, bool]:
        """Normalize a topic label across languages.

        Returns (canonical_key, was_matched). Unmatched text is returned normalized
        as its own key with was_matched=False (never silently merged).
        """
        key = self.canonical_key(text)
        if key:
            return key, True
        norm = _normalize(text)
        return (norm or text), False

    def to_state(self) -> dict:
        from ..models import _now_iso

        return {
            "course_id": self.course_id,
            "terms": self._terms,
            "updated_at": _now_iso(),
        }

    @classmethod
    def from_state(cls, data: dict) -> "TerminologyMap":
        tm = cls(course_id=data.get("course_id", ""))
        tm._terms = dict(data.get("terms", {}) or {})
        tm._rebuild_index()
        return tm


def normalize_topic(topic_text: str, term_map: TerminologyMap) -> tuple[str, bool]:
    """Module-level helper for mixed-language topic normalization."""
    return term_map.resolve_topic(topic_text)
