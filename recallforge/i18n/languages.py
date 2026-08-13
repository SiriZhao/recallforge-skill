from __future__ import annotations

from dataclasses import dataclass, field

from .locales import SUPPORTED_LOCALES


@dataclass
class LanguageProfile:
    """Three distinct language concepts for one user/workspace.

    UI locale       - language the Skill uses to communicate with the user.
    source_languages - languages present in the course materials (may be several).
    output_language - language the user wants generated study material in.

    All three can differ; e.g. UI=zh-CN, materials=en-US, output=zh-CN.
    """

    ui_locale: str = "zh-CN"
    source_languages: list[str] = field(default_factory=list)
    output_language: str = "zh-CN"
    terminology_mode: str = "both"  # "source" | "target" | "both" (bilingual terms)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.ui_locale not in SUPPORTED_LOCALES:
            errors.append(f"unsupported ui_locale: {self.ui_locale!r}")
        if self.output_language not in SUPPORTED_LOCALES:
            errors.append(f"unsupported output_language: {self.output_language!r}")
        for lang in self.source_languages:
            if lang != "auto" and lang not in SUPPORTED_LOCALES:
                errors.append(f"unsupported source language: {lang!r}")
        if self.terminology_mode not in ("source", "target", "both"):
            errors.append(f"invalid terminology_mode: {self.terminology_mode!r}")
        return errors

    def describe(self) -> str:
        """Human summary showing the three concepts explicitly and independently."""
        sources = ", ".join(self.source_languages) if self.source_languages else "auto"
        return (
            f"UI={self.ui_locale} | Source={sources} | Output={self.output_language} "
            f"| Terminology={self.terminology_mode}"
        )
