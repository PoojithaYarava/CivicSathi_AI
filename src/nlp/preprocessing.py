"""Unicode-safe preprocessing and light language heuristics."""

from __future__ import annotations

import re
import unicodedata

import regex

VALID_LANGUAGES = {"English", "Telugu", "Telugu-English", "Unknown"}
_TELUGU = regex.compile(r"\p{Script=Telugu}")
_LATIN = regex.compile(r"\p{Script=Latin}")
_TELUGU_ROMAN_MARKERS = re.compile(
    r"\b(?:ela|cheyyali|cheyali|kavali|kaavali|ki|em|maa|ma|lo|undi|undhi|naaku|naku|kosam|chesukovali)\b",
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace without transliterating/removing script."""
    if not isinstance(text, str):
        raise TypeError(f"query must be str, got {type(text).__name__}")
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u200b", "").replace("\ufeff", "")
    text = re.sub(r"[\r\n\t]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_language(text: str) -> str:
    """Heuristic script label; annotated dataset labels remain authoritative."""
    normalized = normalize_text(text)
    if not normalized:
        return "Unknown"
    has_telugu = bool(_TELUGU.search(normalized))
    has_latin = bool(_LATIN.search(normalized))
    if has_telugu and has_latin:
        return "Telugu-English"
    if has_telugu:
        return "Telugu"
    if has_latin and _TELUGU_ROMAN_MARKERS.search(normalized):
        return "Telugu-English"
    if has_latin and any(ch.isalpha() for ch in normalized):
        return "English"
    return "Unknown"


def validate_language_label(label: str) -> bool:
    return label in VALID_LANGUAGES
