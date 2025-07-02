# Program to create VFX ShotIDs from Marker text file
# made by Seb Riezler

import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime
from io import BytesIO

st.title("VFX ShotID Generator")

st.info("""\
HOW TO:

Add markers to every possible VFX shot. The first shot of each scene or the shot where a change is required is given a MARKER COMMENT, consisting of a number followed by a hyphen.

All locators in between do not need a comment.

    001 -  
    . 
    .
    002 -  
    .
    .
    003 -  
    .
    .

Export the marker list as txt and import in this app.  Happy marking!
""")

uploaded_file = st.file_uploader("Upload a tab-delimited text file (.txt)", type=["txt"])

if not uploaded_file:
    st.markdown(
        '<div style="background-color:#f1f1f1;padding:10px;border-radius:5px; color:#000;">'
        '📁 <strong>Please upload a marker .txt file to begin.</strong>'
        '</div>',
        unsafe_allow_html=True
    )
    
showcode = st.text_input("SHOWCODE (max 5 characters):", value="ABC", max_chars=5).upper()
use_episode = st.checkbox("Add EPISODE code to ShotID")
episode = st.text_input("EPISODE (e.g., E01):", value="E01").upper() if use_episode else ""
if use_episode and episode and not re.match(r"^E\d{2}$", episode):
    st.warning("Episode should be in format E01, E02, etc.")

replace_user = st.checkbox("Replace username")
user_value = st.text_input("Username (e.g., LVB_Seb):", value="").strip() if replace_user else ""
step_size = st.number_input("Increments (freely adjustable)", min_value=1, value=10, step=1)

if uploaded_file:
    try:
        content = uploaded_file.read().decode("utf-8")
        base_filename = os.path.splitext(uploaded_file.name)[0]
        lines = content.strip().split("\n")

        original_lines = []
        marker_codes = []
        last_seen_marker = ""

        for line in lines:
            fields = line.strip().split("\t")
            if not fields or all(f.strip() == "" for f in fields):
                continue
            original_lines.append(fields)
            marker_field = fields[4].strip() if len(fields) > 4 else ""
            match = re.match(r"^(\d{3})\s*-", marker_field)
            if match:
                last_seen_marker = match.group(1)
                marker_codes.append(last_seen_marker)
            elif last_seen_marker:
                marker_codes.append(last_seen_marker)
            else:
                marker_codes.append("")

        grouped = {}
        labeled_codes = []

        for marker in marker_codes:
            if not marker:
                labeled_codes.append("")
                continue
            if marker not in grouped:
                grouped[marker] = step_size
            counter = grouped[marker]
            label = f"{showcode}_{episode + '_' if use_episode else ''}{marker}_{str(counter).zfill(4)}"
            labeled_codes.append(label)
            grouped[marker] += step_size

        preview_lines = []
        for i, fields in enumerate(original_lines):
            new_fields = fields[:]
            while len(new_fields) < 1:
                new_fields.append("")
            if user_value:
                new_fields[0] = user_value
            while len(new_fields) < 7:
                new_fields.append("")
            new_fields[4] = labeled_codes[i] or new_fields[4]
            preview_lines.append(new_fields)

        # Vorschau
        st.subheader("Original File Preview")
        st.dataframe(original_lines[:50], use_container_width=True)

        st.subheader("Processed File Preview")
        st.dataframe(preview_lines[:50], use_container_width=True)

        # Export Dropdown + Button
        st.subheader("Export")
        export_format = st.selectbox("Choose export format:", [
            "Plain Text (.txt)",
            "CSV (comma-separated)",
            "CSV (semicolon-separated)",
            "Google Sheets (via CSV)",
            "Apple Numbers (via CSV)"
        ])

        export_df = pd.DataFrame(preview_lines)
        output_lines = ["\t".join(fields) for fields in preview_lines]
        output_str = "\n".join(output_lines)
        timestamp = datetime.now().strftime("%Y%m%d")
        csv_comma = export_df.to_csv(index=False)
        csv_semicolon = export_df.to_csv(index=False, sep=";")

        if export_format == "Plain Text (.txt)":
            st.download_button("Export", output_str, file_name=f"{base_filename}_{timestamp}.txt", mime="text/plain")
        elif export_format == "CSV (comma-separated)":
            st.download_button("Export", csv_comma, file_name=f"{base_filename}_{timestamp}.csv", mime="text/csv")
        elif export_format == "CSV (semicolon-separated)":
            st.download_button("Export", csv_semicolon, file_name=f"{base_filename}_semicolon_{timestamp}.csv", mime="text/csv")
        elif export_format == "Google Sheets (via CSV)":
            st.download_button("Export", csv_comma, file_name=f"{base_filename}_GSheets_{timestamp}.csv", mime="text/csv")
        elif export_format == "Apple Numbers (via CSV)":
            st.download_button("Export", csv_semicolon, file_name=f"{base_filename}_Numbers_{timestamp}.csv", mime="text/csv")

    except Exception as e:
        st.error(f"An error occurred: {e}")



