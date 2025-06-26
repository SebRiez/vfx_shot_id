# Program to create VFX ShotIDs from Marker text file
# made by Seb Riezler
import streamlit as st
import re
import io
import os
import pandas as pd

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

showcode = st.text_input("SHOWCODE (3 characters):", value="ABC", max_chars=3).upper()

# Episoden-Schalter
use_episode = st.checkbox("Add EPISODE code to ShotID")
episode = ""
if use_episode:
    episode = st.text_input("EPISODE (e.g., E01):", value="E01").upper()

step_size = st.number_input("Increments (freely adjustable)", min_value=1, value=1, step=1)

if uploaded_file:
    content = uploaded_file.read().decode("utf-8")
    filename = uploaded_file.name
    base_filename = os.path.splitext(filename)[0]
    lines = content.split("\n")
    original_lines = []
    marker_codes = []
    last_seen_marker = ""

    for line in lines:
        fields = line.strip().split("\t")
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
        if use_episode:
            label = f"{showcode}_{episode}_{marker}_{str(counter).zfill(4)}"
        else:
            label = f"{showcode}_{marker}_{str(counter).zfill(4)}"
        labeled_codes.append(label)
        grouped[marker] += step_size

    # Display original preview
    st.subheader("Original File Preview")
    st.dataframe(original_lines[:50], use_container_width=True)

    # Prepare modified preview
    preview_lines = []
    for i, fields in enumerate(original_lines):
        new_fields = fields[:]
        while len(new_fields) < 7:
            new_fields.append("")
        new_fields[4] = labeled_codes[i] or new_fields[4]
        preview_lines.append(new_fields)

    st.write(f"Total lines: {len(preview_lines)}")

    # DataFrame for styling
    df = pd.DataFrame(preview_lines[:50])

    def highlight_marker_column(val, col_index):
        if col_index == 4:
            return 'background-color: #d0ebff; color: black'
        return ''

    styled_df = df.style.apply(lambda row: [highlight_marker_column(val, i) for i, val in enumerate(row)], axis=1)
    st.subheader("Processed File Preview (highlighted changes)")
    st.dataframe(styled_df, use_container_width=True)

    # Prepare download
    output_lines = ["\t".join(fields) for fields in preview_lines]
    output_str = "\n".join(output_lines)
    download_filename = f"{base_filename}_processed.txt"
    st.download_button("Save as .txt", output_str, file_name=download_filename, mime="text/plain")
