"""Internationalization foundation for recallforge-skill v2.

Three distinct language concepts are modeled separately:
  * UI locale      - the language used to talk to the user (Skill language)
  * source language - the language of the course materials (per evidence/course)
  * output language - the language the user wants generated study material in

All internal schema keys are stable English identifiers; localization happens only
at the UI/output boundary via locale catalogs.
"""

from .languages import LanguageProfile
from .locales import SUPPORTED_LOCALES, get_catalog, register_locale, t
from .terminology import TerminologyMap, normalize_topic
from .output_modes import OutputMode, render_bilingual

__all__ = [
    "LanguageProfile",
    "OutputMode",
    "SUPPORTED_LOCALES",
    "TerminologyMap",
    "get_catalog",
    "normalize_topic",
    "render_bilingual",
    "register_locale",
    "t",
]
