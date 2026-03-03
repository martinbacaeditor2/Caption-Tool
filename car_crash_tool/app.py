from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from streamlit.components.v1 import html

from excel_export import append_to_existing_xlsx, export_new_xlsx
from generator import generate_content, regenerate_language


load_dotenv()
st.set_page_config(page_title="Car Crash Legal Content Generator", layout="wide")


if "payload" not in st.session_state:
    st.session_state.payload = None
if "validation" not in st.session_state:
    st.session_state.validation = None


def copy_button(value: str, label: str):
    uid = f"copy_{uuid.uuid4().hex}"
    safe = json.dumps(value)
    html(
        f"""
        <button id="{uid}" style="padding:6px 10px;border-radius:8px;border:1px solid #ccc;cursor:pointer;">{label}</button>
        <script>
        const btn = document.getElementById('{uid}');
        btn.onclick = async () => {{
          try {{
            await navigator.clipboard.writeText({safe});
            btn.innerText = 'Copied!';
            setTimeout(() => btn.innerText = '{label}', 1200);
          }} catch(e) {{
            btn.innerText = 'Copy failed';
          }}
        }};
        </script>
        """,
        height=42,
    )


st.title("Car Crash Legal Content Generator")
st.caption("Generate EN/ES structured legal-social content and export directly to Excel planner format.")

api_key = st.text_input("OpenAI API Key", value=os.getenv("OPENAI_API_KEY", ""), type="password")
uploaded_image = st.file_uploader("Upload thumbnail image", type=["jpg", "jpeg", "png"])
notes = st.text_area("Optional notes", placeholder="Any context or angle you want reflected in the tone...")

col_gen, col_clear = st.columns([1, 1])
with col_gen:
    generate_clicked = st.button("Generate", type="primary", use_container_width=True)
with col_clear:
    if st.button("Clear", use_container_width=True):
        st.session_state.payload = None
        st.session_state.validation = None
        st.rerun()

if generate_clicked:
    if not api_key:
        st.error("Please provide an OpenAI API Key.")
    elif not uploaded_image:
        st.error("Please upload an image first.")
    else:
        with st.spinner("Generating bilingual content..."):
            image_bytes = uploaded_image.getvalue()
            mime_type = uploaded_image.type or "image/jpeg"
            payload, checks = generate_content(image_bytes, mime_type, notes, api_key)
            st.session_state.payload = payload
            st.session_state.validation = checks

payload = st.session_state.payload
checks = st.session_state.validation

if payload:
    if checks and any(checks.values()):
        st.warning("Some validation rules still need attention. You can regenerate per language.")

    for lang in ["EN", "ES"]:
        st.subheader(f"{lang} Result")
        block = payload.get(lang, {})

        if checks and checks.get(lang):
            st.error("; ".join(checks[lang]))

        c1, c2 = st.columns([3, 1])
        with c1:
            st.text_input(f"{lang} internal_name", value=block.get("internal_name", ""), key=f"{lang}_internal", disabled=True)
        with c2:
            copy_button(block.get("internal_name", ""), "Copy internal_name")

        c1, c2 = st.columns([3, 1])
        with c1:
            st.text_area(f"{lang} video_caption", value=block.get("video_caption", ""), key=f"{lang}_vcap", disabled=True, height=80)
        with c2:
            copy_button(block.get("video_caption", ""), "Copy video_caption")

        c1, c2 = st.columns([3, 1])
        with c1:
            st.text_area(f"{lang} post_description", value=block.get("post_description", ""), key=f"{lang}_pdesc", disabled=True, height=230)
        with c2:
            copy_button(block.get("post_description", ""), "Copy post_description")

        c1, c2 = st.columns([3, 1])
        with c1:
            st.text_input(f"{lang} thumbnail_text", value=block.get("thumbnail_text", ""), key=f"{lang}_thumb", disabled=True)
        with c2:
            copy_button(block.get("thumbnail_text", ""), "Copy thumbnail_text")

        if st.button(f"Regenerate {lang}", key=f"regen_{lang}"):
            with st.spinner(f"Regenerating {lang}..."):
                image_bytes = uploaded_image.getvalue() if uploaded_image else b""
                mime_type = uploaded_image.type if uploaded_image else "image/jpeg"
                updated_payload, lang_errors = regenerate_language(
                    lang, payload, image_bytes, mime_type, notes, api_key
                )
                st.session_state.payload = updated_payload
                if not st.session_state.validation:
                    st.session_state.validation = {}
                st.session_state.validation[lang] = lang_errors
            st.rerun()

    st.divider()
    st.subheader("Export to Excel")
    export_mode = st.radio("Export mode", ["Create new XLSX", "Append to existing planner"], horizontal=True)

    if export_mode == "Create new XLSX":
        new_name = st.text_input("Output file name", value="planner_output.xlsx")
        if st.button("Export new XLSX", type="primary"):
            out = export_new_xlsx(payload, Path(new_name))
            st.success(f"Saved: {out}")
    else:
        existing = st.text_input("Existing planner path", value="planner.xlsx")
        save_as = st.text_input("Optional output file (leave blank to overwrite existing)", value="")
        if st.button("Append to planner", type="primary"):
            out = append_to_existing_xlsx(payload, existing, save_as or None)
            st.success(f"Saved: {out}")
