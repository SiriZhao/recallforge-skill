from __future__ import annotations


class OutputMode:
    """Three output modes. Bilingual means Chinese main text with English key
    terms (or the user-specified arrangement) - never every sentence twice."""

    CHINESE = "chinese"
    ENGLISH = "english"
    BILINGUAL = "bilingual"

    @classmethod
    def parse(cls, value: str | None) -> str:
        if not value:
            return cls.BILINGUAL
        normalized = value.strip().lower().replace("-", "").replace("_", "")
        mapping = {
            "chinese": cls.CHINESE,
            "zh": cls.CHINESE,
            "zhcn": cls.CHINESE,
            "cn": cls.CHINESE,
            "english": cls.ENGLISH,
            "en": cls.ENGLISH,
            "enus": cls.ENGLISH,
            "us": cls.ENGLISH,
            "bilingual": cls.BILINGUAL,
            "both": cls.BILINGUAL,
            "bi": cls.BILINGUAL,
        }
        if normalized not in mapping:
            raise ValueError(
                f"invalid output mode {value!r}; expected chinese/english/bilingual"
            )
        return mapping[normalized]


def render_bilingual(
    *,
    zh: str,
    en: str,
    mode: str,
    term_map=None,
    term_key: str | None = None,
    primary: str = "zh",
) -> str:
    """Render text in the requested output mode.

    Chinese/English: single language.
    Bilingual: Chinese main text with the English key term appended in
    parentheses (or primary=english reverses it). Never duplicates sentences.
    """
    mode = OutputMode.parse(mode)
    if mode == OutputMode.CHINESE:
        return zh
    if mode == OutputMode.ENGLISH:
        return en

    # bilingual: main text + key TERM, never full sentence duplication
    term = None
    if term_key and term_map:
        localized_term = term_map.localize(term_key, "en-US" if primary == "zh" else "zh-CN")
        if localized_term:
            term = localized_term
    if term is None:
        # no map entry: only use the other-language text if it is a short term
        other = en if primary == "zh" else zh
        if len(other) <= 40 and "\n" not in other:
            term = other.strip()
    if term is None:
        # too long to be a term: do NOT duplicate sentences, main text only
        return zh if primary == "zh" else en
    if primary == "zh":
        return f"{zh}（{term}）"
    return f"{en} ({term})"
