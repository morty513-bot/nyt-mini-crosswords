from __future__ import annotations

REJECTED_WORDS = {
    "apr",
    "aug",
    "dec",
    "debra",
    "delhi",
    "dvd",
    "feb",
    "fax",
    "jan",
    "jul",
    "jun",
    "nov",
    "oct",
    "pdf",
    "pda",
    "sep",
    "sept",
    "usa",
    "hugo",
}

MIN_ZIPF_FREQUENCY = 4.3


def normalize_word(value: str) -> str:
    return value.strip().lower()


def is_allowed_word(word: str, zipf_frequency: float) -> bool:
    normalized = normalize_word(word)
    if not normalized or not normalized.isalpha():
        return False
    if len(normalized) < 3 or len(normalized) > 5:
        return False
    if normalized in REJECTED_WORDS:
        return False
    return zipf_frequency >= MIN_ZIPF_FREQUENCY
