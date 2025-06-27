# Program to create VFX ShotIDs from Marker text file
# made by Seb Riezler
# Program to create VFX ShotIDs from Marker text file
# made by Seb Riezler

# Program to create VFX ShotIDs from Marker text file
# made by Seb Riezler

import streamlit as st
import re
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

# Upload input file
uploaded_file = st.file_uploader("Upload a tab-delimited text file (.txt)", type=["txt"])

# Input fields
showcode = st.text_input("SHOWCODE (3 chars):", value="", max_chars=3).upper()

# Episoden-Schalter
use_episode = st.checkbox("add EPISODE code to ShotID")
episode = ""
if use_episode:
    episode = st.text_input("EPISODE (e.g., E01):", value="E01").upper()

# Username-Ersetzung (optional)
replace_user = st.checkbox("Replace username")
user_value = ""
if replace_user:
    user_value = st.text_input("Username (e.g., VFX-EDITOR):", value="").strip()

# Schrittgröße (Inkremente)
step_size = st.number_input("Increments (freely adjustable)", min_value=1, value=10, step=1)

# Wenn Datei hochgeladen wurde
if uploaded_file:
    content = uploaded_file.read().decode("utf-8")
    filename = uploaded_file.name
    base_filename = os.path.splitext(filename)[0]
    lines = content.split("\n")
    original_lines = []
    marker_codes = []
    last_seen_marker = ""

    # Einlesen & Marker erkennen
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

    # ShotIDs erzeugen
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

    import streamlit.components.v1 as components

st.subheader("Preview: Original vs. Processed")

# DataFrames erstellen
original_df = pd.DataFrame(original_lines[:50])
processed_df = pd.DataFrame(preview_lines[:50])

# Tabellen in HTML mit Scroll-Synchronisation
original_html = original_df.to_html(index=False)
processed_html = pd.DataFrame(preview_lines[:50]).style.apply(
    lambda row: ['background-color: #d0ebff; color: black' if i == 4 else '' for i in range(len(row))],
    axis=1
).to_html(index=False)

# Kombinierte HTML mit synchronem Scrollen
combined_html = f"""
<style>
.scroll-table {{
    overflow-x: auto;
    overflow-y: scroll;
    height: 500px;
    width: 100%;
}}
.table-wrapper {{
    display: flex;
    gap: 20px;
}}
.table-wrapper table {{
    font-size: 12px;
    min-width: 400px;
    border-collapse: collapse;
}}
th, td {{
    padding: 4px;
    border: 1px solid #ccc;
}}
</style>

<div class="table-wrapper">
    <div class="scroll-table" id="table1">{original_html}</div>
    <div class="scroll-table" id="table2">{processed_html}</div>
</div>

<script>
const t1 = document.getElementById('table1');
const t2 = document.getElementById('table2');
let isSyncing = false;
function syncScroll(source, target) {{
    if (!isSyncing) {{
        isSyncing = true;
        target.scrollTop = source.scrollTop;
        setTimeout(() => isSyncing = false, 20);
    }}
}}
t1.onscroll = () => syncScroll(t1, t2);
t2.onscroll = () => syncScroll(t2, t1);
</script>
"""

# Anzeigen
components.html(combined_html, height=520, scrolling=False)


    # Datei zum Download vorbereiten
    output_lines = ["\t".join(fields) for fields in preview_lines]
    output_str = "\n".join(output_lines)
    download_filename = f"{base_filename}_processed.txt"

    st.download_button("Save as .txt", output_str, file_name=download_filename, mime="text/plain")
