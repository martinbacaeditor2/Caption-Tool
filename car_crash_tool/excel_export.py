from __future__ import annotations

from pathlib import Path

import pandas as pd


OUTPUT_COLUMNS = ["Nombre del Video", "Idioma", "Caption", "Video Caption", "Thumbnail"]


def payload_to_rows(payload: dict) -> list[dict]:
    rows: list[dict] = []
    for lang in ["EN", "ES"]:
        block = payload.get(lang, {})
        rows.append(
            {
                "Nombre del Video": block.get("internal_name", ""),
                "Idioma": lang,
                "Caption": block.get("post_description", ""),
                "Video Caption": block.get("video_caption", ""),
                "Thumbnail": block.get("thumbnail_text", ""),
            }
        )
    return rows


def export_new_xlsx(payload: dict, output_path: str | Path) -> Path:
    path = Path(output_path)
    df = pd.DataFrame(payload_to_rows(payload), columns=OUTPUT_COLUMNS)
    df.to_excel(path, index=False)
    return path


def append_to_existing_xlsx(payload: dict, existing_path: str | Path, output_path: str | Path | None = None) -> Path:
    existing = Path(existing_path)
    out = Path(output_path) if output_path else existing

    if existing.exists():
        old = pd.read_excel(existing)
    else:
        old = pd.DataFrame(columns=OUTPUT_COLUMNS)

    for col in OUTPUT_COLUMNS:
        if col not in old.columns:
            old[col] = ""

    new_df = pd.DataFrame(payload_to_rows(payload), columns=OUTPUT_COLUMNS)
    merged = pd.concat([old[OUTPUT_COLUMNS], new_df], ignore_index=True)
    merged.to_excel(out, index=False)
    return out
