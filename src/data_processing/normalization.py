"""Multilingual-safe text and URL normalization."""

from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

import pandas as pd

TELUGU_RE = re.compile(r"[\u0C00-\u0C7F]")
LATIN_RE = re.compile(r"[A-Za-z]")
ROMANIZED_TELUGU_RE = re.compile(r"\b(ela|cheyyali|cheyali|kavali|enti|ekkada|undi|unnayi|maa|naaku|naku|kosam|cheppandi|ivvali|avutondi|ledu|lo|ki)\b", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\w)")
AADHAAR_RE = re.compile(r"(?<!\d)(?:\d[ -]?){11}\d(?!\d)")
PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.IGNORECASE)
CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
OTP_RE = re.compile(r"\b\d{4,8}\s*(?:otp|one[- ]time password)\b|\b(?:otp|one[- ]time password)\s*[:=-]?\s*\d{4,8}\b", re.IGNORECASE)


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", text).strip()


def detect_language(value: object) -> str:
    text = clean_text(value)
    has_telugu, has_latin = bool(TELUGU_RE.search(text)), bool(LATIN_RE.search(text))
    if (has_telugu and has_latin) or (has_latin and ROMANIZED_TELUGU_RE.search(text)):
        return "Telugu-English"
    if has_telugu:
        return "Telugu"
    if has_latin:
        return "English"
    return "Unknown"


def normalize_url(value: object) -> str:
    text = clean_text(value)
    if not text:
        return ""
    try:
        parts = urlsplit(text)
    except ValueError:
        return ""
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        return ""
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, ""))


def find_sensitive_patterns(value: object) -> list[str]:
    text = clean_text(value)
    patterns = (
        ("email", EMAIL_RE), ("phone", PHONE_RE), ("aadhaar_like", AADHAAR_RE),
        ("pan_like", PAN_RE), ("card_like", CARD_RE), ("otp_like", OTP_RE),
    )
    return [label for label, pattern in patterns if pattern.search(text)]