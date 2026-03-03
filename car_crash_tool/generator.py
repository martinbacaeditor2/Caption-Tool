import base64
import json
from typing import Any

from openai import OpenAI

from prompts import SYSTEM_PROMPT, build_regen_prompt, build_user_prompt
from validator import validate_payload


MODEL = "gpt-4.1-mini"


def _to_data_url(image_bytes: bytes, mime_type: str) -> str:
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def _call_model(client: OpenAI, user_text: str, image_bytes: bytes, mime_type: str) -> dict[str, Any]:
    response = client.responses.create(
        model=MODEL,
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": SYSTEM_PROMPT}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": user_text},
                    {"type": "input_image", "image_url": _to_data_url(image_bytes, mime_type)},
                ],
            },
        ],
    )
    return _parse_json(response.output_text)


def generate_content(
    image_bytes: bytes,
    mime_type: str,
    optional_notes: str | None,
    api_key: str,
    max_regen_attempts: int = 2,
) -> tuple[dict[str, Any], dict[str, list[str]]]:
    client = OpenAI(api_key=api_key)
    payload = _call_model(client, build_user_prompt(optional_notes), image_bytes, mime_type)

    checks = validate_payload(payload)
    for _ in range(max_regen_attempts):
        invalid_langs = [lang for lang, errs in checks.items() if errs]
        if not invalid_langs:
            break

        for lang in invalid_langs:
            reason = "; ".join(checks[lang])
            regen_prompt = build_regen_prompt(lang, payload, reason)
            updated = _call_model(client, regen_prompt, image_bytes, mime_type)
            if isinstance(updated, dict) and lang in updated and isinstance(updated[lang], dict):
                payload[lang] = updated[lang]

        checks = validate_payload(payload)

    return payload, checks


def regenerate_language(
    language: str,
    current_payload: dict[str, Any],
    image_bytes: bytes,
    mime_type: str,
    optional_notes: str | None,
    api_key: str,
) -> tuple[dict[str, Any], list[str]]:
    client = OpenAI(api_key=api_key)
    reason = "Manual regeneration requested by user while keeping all mandatory constraints."
    prompt = build_regen_prompt(language, current_payload, reason) + "\n" + build_user_prompt(optional_notes)
    updated = _call_model(client, prompt, image_bytes, mime_type)

    if isinstance(updated, dict) and language in updated and isinstance(updated[language], dict):
        current_payload[language] = updated[language]

    checks = validate_payload(current_payload)
    return current_payload, checks.get(language, [])
