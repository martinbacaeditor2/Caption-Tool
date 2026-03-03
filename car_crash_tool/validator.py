import re
from typing import Any

BRANDS = {"EN": "Broadway Law", "ES": "Abogados de Accidentes"}
FORBIDDEN_BRANDS = {
    "EN": ["Abogados de Accidentes"],
    "ES": ["Broadway Law"],
}


def _is_pascal_case(text: str) -> bool:
    return bool(re.fullmatch(r"[A-Z][a-zA-Z0-9]*", text))


def _validate_internal_name(language: str, value: str) -> str | None:
    if not isinstance(value, str):
        return "internal_name must be a string"
    if not value.startswith(f"{language}-"):
        return f"internal_name must start with {language}-"
    base = value.split("-", 1)[1]
    if "-" in base or " " in base:
        return "BaseName must not contain spaces or hyphens"
    if not _is_pascal_case(base):
        return "BaseName must be PascalCase"
    return None


def _validate_thumbnail_text(value: str) -> str | None:
    if not isinstance(value, str):
        return "thumbnail_text must be a string"
    words = [w for w in value.strip().split() if w]
    if len(words) < 2 or len(words) > 5:
        return "thumbnail_text must have 2 to 5 words"
    caps = [w for w in words if re.fullmatch(r"[A-Z0-9]+", w)]
    if len(caps) != 1:
        return "thumbnail_text must contain exactly one ALL CAPS word"
    if "\n" in value:
        return "thumbnail_text must be a single line"
    return None


def _validate_video_caption(value: str, language: str) -> str | None:
    if not isinstance(value, str):
        return "video_caption must be a string"
    if len([ln for ln in value.splitlines() if ln.strip()]) > 2:
        return "video_caption must be max 2 lines"
    if BRANDS[language].lower() in value.lower():
        return "video_caption must not contain the brand"
    return None


def _validate_post_description(value: str, language: str) -> str | None:
    if not isinstance(value, str):
        return "post_description must be a string"
    brand = BRANDS[language]
    if brand.lower() not in value.lower():
        return f"post_description must contain {brand}"
    for forbidden in FORBIDDEN_BRANDS[language]:
        if forbidden.lower() in value.lower():
            return f"post_description must not contain {forbidden}"
    blocks = [b for b in value.split("\n\n") if b.strip()]
    if len(blocks) < 4:
        return "post_description must include 3 paragraphs plus hashtag block"
    hashtags = re.findall(r"#[\wÁÉÍÓÚáéíóúÑñ]+", value)
    if len(hashtags) < 8 or len(hashtags) > 14:
        return "post_description must contain 8 to 14 hashtags"
    return None


def validate_language_block(language: str, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ["internal_name", "video_caption", "post_description", "thumbnail_text"]:
        if field not in data:
            errors.append(f"Missing field: {field}")
    if errors:
        return errors

    checks = [
        _validate_internal_name(language, data["internal_name"]),
        _validate_video_caption(data["video_caption"], language),
        _validate_post_description(data["post_description"], language),
        _validate_thumbnail_text(data["thumbnail_text"]),
    ]
    errors.extend([c for c in checks if c])
    return errors


def validate_payload(payload: dict[str, Any]) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {}
    for lang in ["EN", "ES"]:
        block = payload.get(lang)
        if not isinstance(block, dict):
            results[lang] = [f"Missing or invalid {lang} object"]
            continue
        results[lang] = validate_language_block(lang, block)
    return results


def is_valid(payload: dict[str, Any]) -> bool:
    checks = validate_payload(payload)
    return all(len(v) == 0 for v in checks.values())
