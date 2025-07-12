# VFX ShotID Generator
# by Seb Riezler – verbessert für Avid-kompatiblen Export

import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime

st.title("🎬 VFX ShotID Generator")

st.info("""\
**HOW TO:**

1. In your editing software, add a marker to every potential VFX shot.
2. The first marker of each section/ scene gets a comment with a number followed by a dash:

    Marker Comment: 001 -  
    .
    .
    .
    
    Marker Comment: 002 -  
    .
    .
    .
    
    Marker Comment: 003 -  
    .
    .
    .
    


3. Export the markers as a **tab-delimited text file** (.txt) and upload it below.
""")

# File Upload
uploaded_file = st.file_uploader("📁 Upload tab-delimited marker file (.txt)", type=["txt"])

# ShotID Einstellungen
showcode = st.text_input("🎬 SHOWCODE (max 5 characters):", value="MUM", max_chars=5).upper()
use_episode = st.checkbox("🔢 Add EPISODE code to ShotID")
episode = st.text_input("Episode (e.g., E01):", value="E01").upper() if use_episode else ""
if use_episode and episode and not re.match(r"^E\d{2}$", episode):
    st.warning("⚠️ Episode should be in format E01, E02, etc.")

# Username Steuerung
replace_user = st.checkbox("✏️ Replace username in column 1")
user_value = st.text_input("Custom Username (e.g., VFX-EDITOR):", value="").strip() if replace_user else ""

# Schrittweite
step_size = st.number_input("Increments (freely adjustable)", min_value=1, value=10, step=1)

if uploaded_file:
    try:
        content = uploaded_file.read().decode("utf-8")
        base_filename = os.path.splitext(uploaded_file.name)[0]
        lines = content.strip().split("\n")

        original_lines = []
        marker_codes = []
        last_seen_marker = ""

        # Parsing der Originaldaten + Markerextraktion
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

        # ShotID-Generierung
        grouped = {}
        labeled_codes = []

        for marker in marker_codes:
            if not marker:
                labeled_codes.append("")
                continue
            if marker not in grouped:
                grouped[marker] = step_size
            counter = grouped[marker]
            shot_id = f"{showcode}_{episode + '_' if use_episode else ''}{marker}_{str(counter).zfill(4)}"
            labeled_codes.append(shot_id)
            grouped[marker] += step_size

        # Hilfsfunktion zur Längen-Sicherung
        def ensure_length(lst, length):
            return lst + [""] * (length - len(lst)) if len(lst) < length else lst[:length]

        # Verarbeitete Zeilen bauen
        preview_lines = []
        for i, fields in enumerate(original_lines):
            fields = ensure_length(fields, 8)
            new_fields = fields[:]

            # Benutzername setzen (aus Feld oder ersetzt)
            if replace_user and user_value:
                new_fields[0] = user_value
            else:
                new_fields[0] = fields[0]

            # ShotID einsetzen
            if labeled_codes[i]:
                new_fields[4] = labeled_codes[i]

            preview_lines.append(new_fields)

        # Vorschau anzeigen
        st.subheader("📄 Original File Preview")
        st.dataframe(original_lines[:50], use_container_width=True)

        st.subheader("✅ Processed File Preview")
        st.dataframe(preview_lines[:50], use_container_width=True)

        # Exportoptionen
        st.subheader("⬇️ Export")
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

        export_filename = f"{base_filename}_{timestamp}"

        if export_format == "Plain Text (.txt)":
            st.download_button("📥 Download .txt", output_str, file_name=f"{export_filename}.txt", mime="text/plain")
        elif export_format == "CSV (comma-separated)":
            st.download_button("📥 Download CSV", csv_comma, file_name=f"{export_filename}.csv", mime="text/csv")
        elif export_format == "CSV (semicolon-separated)":
            st.download_button("📥 Download CSV (;)", csv_semicolon, file_name=f"{export_filename}_semicolon.csv", mime="text/csv")
        elif export_format == "Google Sheets (via CSV)":
            st.download_button("📥 Download GSheets CSV", csv_comma, file_name=f"{export_filename}_GSheets.csv", mime="text/csv")
        elif export_format == "Apple Numbers (via CSV)":
            st.download_button("📥 Download Numbers CSV", csv_semicolon, file_name=f"{export_filename}_Numbers.csv", mime="text/csv")

    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
else:
    st.markdown(
        '<div style="background-color:#f1f1f1;padding:10px;border-radius:5px; color:#000;">'
        '📁 <strong>Please upload a marker .txt file to begin.</strong>'
        '</div>',
        unsafe_allow_html=True
    )
