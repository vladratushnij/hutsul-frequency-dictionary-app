from __future__ import annotations

import re
from pathlib import Path


APOSTROPHES = {
    "`": "’",
    "'": "’",
    "ʼ": "’",
    "՚": "’",
    "‘": "’",
    "’": "’",
}


def normalize_lexeme(text: object) -> str:
    """Normalize a lexeme for matching without changing ґ to г."""
    if text is None:
        return ""
    value = str(text).strip().lower()
    for old, new in APOSTROPHES.items():
        value = value.replace(old, new)
    value = value.replace("‐", "-").replace("‑", "-").replace("–", "-").replace("—", "-")
    value = re.sub(r"\s+", " ", value)
    value = value.strip(" \t\r\n\"“”„«»[]{}()<>.,;:!?/\\|")
    return value


def is_service_token(text: object) -> bool:
    value = normalize_lexeme(text)
    if not value:
        return True
    if re.fullmatch(r"[\W_]+", value, flags=re.UNICODE):
        return True
    if re.fullmatch(r"\d+([.,:/-]\d+)*", value):
        return True
    if re.fullmatch(r"\d{2,4}(-\d{2,4})?", value):
        return True
    if not re.search(r"[а-щьюяєіїґ]", value):
        return True
    return False


def ensure_output_dir(path: str | Path = "output") -> Path:
    output = Path(path)
    output.mkdir(parents=True, exist_ok=True)
    return output


def safe_frequency(value: object) -> int:
    try:
        if value is None or str(value).strip() == "":
            return 0
        return int(float(str(value).replace(",", ".")))
    except ValueError:
        return 0

