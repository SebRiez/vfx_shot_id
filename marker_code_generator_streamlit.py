# VFX ShotID Generator
# by Seb Riezler – erweitert für TXT + Premiere XML (Clip Marker)

import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime
import xml.etree.ElementTree as ET  # Für XML-Parsing

st.markdown(
    "<h1 style='text-align: center;'>🎬 VFX ShotID Generator</h1>",
    unsafe_allow_html=True
)

# File Upload – TXT + XML
uploaded_file = st.file_uploader(
    "📁 Upload marker file (.txt or Premiere XML)",
    type=["txt", "xml"]
)

# ShotID Einstellungen
showcode = st.text_input(
    "🎬 SHOWCODE (max 5 characters):",
    value="ABCDE",
    max_chars=5
).upper()

use_episode = st.checkbox("🔢 Add EPISODE code to ShotID (separated by _ )")
episode = st.text_input("Episode (e.g., E01):", value="E01").upper() if use_episode else ""
if use_episode and episode and not re.match(r"^E\d{2}$", episode):
    st.warning("⚠️ Episode should be in format E01, E02, etc.")

# Username Steuerung
replace_user = st.checkbox("✏️ Replace username")
user_value = (
    st.text_input("Custom Username (e.g., VFX-EDITOR):", value="").strip()
    if replace_user else ""
)

# Schrittweite
step_size = st.number_input(
    "Increments (freely adjustable)",
    min_value=1,
    value=10,
    step=1
)

if uploaded_file:
    try:
        base_filename = os.path.splitext(uploaded_file.name)[0]
        ext = os.path.splitext(uploaded_file.name)[1].lower()

        original_lines = []

        # ---------------------------------------------------------
        # TXT-Pfad: tab-getrennte Markerdatei wie bisher
        # ---------------------------------------------------------
        if ext == ".txt":
            content = uploaded_file.read().decode("utf-8", errors="ignore")
            lines = content.strip().split("\n")

            for line in lines:
                fields = line.strip().split("\t")
                if not fields or all(f.strip() == "" for f in fields):
                    continue
                original_lines.append(fields)

        # ---------------------------------------------------------
        # XML-Pfad: Premiere/FCP-XML mit Clip-Markern
        # (Struktur anhand der Beispiel-XML)
        # ---------------------------------------------------------
        elif ext == ".xml":
            raw_bytes = uploaded_file.read()
            root = ET.fromstring(raw_bytes)

            default_username = ""

            # Alle Clipitems in den Video-Tracks
            # (sequence/media/video/track/clipitem)
            for clipitem in root.findall(".//sequence/media/video//clipitem"):
                clip_name = (clipitem.findtext("name", "") or "").strip()
                seq_start = (clipitem.findtext("start", "") or "").strip()
                seq_end = (clipitem.findtext("end", "") or "").strip()

                # Marker innerhalb dieses Clips (Clip Marker)
                for marker in clipitem.findall("marker"):
                    m_name = (marker.findtext("name", "") or "").strip()
                    m_comment = (marker.findtext("comment", "") or "").strip()
                    m_in = (marker.findtext("in", "") or "").strip()
                    m_out = (marker.findtext("out", "") or "").strip()

                    # Markertext priorisieren: "name comment"
                    if m_comment:
                        marker_text = f"{m_name} {m_comment}".strip()
                    else:
                        marker_text = m_name

                    # 8 Felder, damit die Struktur zum TXT-Parsing passt
                    # Wichtig: fields[4] = Marker-Text (für dein Regex)
                    fields = [
                        default_username,  # 0: Username (wird später ersetzt)
                        clip_name,         # 1: Clip-Name
                        m_in,              # 2: Marker-In (Frames)
                        m_out,             # 3: Marker-Out
                        marker_text,       # 4: Marker-Text (z.B. "001 -")
                        m_comment,         # 5: Kommentar
                        seq_start,         # 6: Clip Start in Sequence
                        seq_end            # 7: Clip End in Sequence
                    ]
                    original_lines.append(fields)

            if not original_lines:
                st.warning("⚠️ No markers found in XML file. Check Premiere export settings.")

        else:
            st.error("❌ Unsupported file type. Please upload .txt or Premiere XML.")
            original_lines = []

        if not original_lines:
            st.stop()

        # ---------------------------------------------------------
        # Gemeinsame Verarbeitung (TXT + XML)
        # Marker-Codes extrahieren (001, 002, … aus Feld 4)
        # ---------------------------------------------------------
        marker_codes = []
        last_seen_marker = ""

        for fields in original_lines:
            if len(fields) > 4:
                marker_field = fields[4].strip()
            else:
                marker_field = ""

            # Muster: "001 -" (erste 3 Ziffern + Bindestrich)
            match = re.match(r"^(\d{3})\s*-", marker_field)
            if match:
                last_seen_marker = match.group(1)
                marker_codes.append(last_seen_marker)
            elif last_seen_marker:
                # Zeile gehört noch zum vorherigen Marker-Block
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
            if i < len(labeled_codes) and labeled_codes[i]:
                new_fields[4] = labeled_codes[i]

            preview_lines.append(new_fields)

        # ---------------------------------------------------------
        # Vorschau
        # ---------------------------------------------------------
        st.subheader("📄 Original File Preview")
        st.dataframe(original_lines[:50], use_container_width=True)

        st.subheader("✅ Processed File Preview")
        st.dataframe(preview_lines[:50], use_container_width=True)

        # ---------------------------------------------------------
        # Exportoptionen
        # ---------------------------------------------------------
        st.subheader("⬇️ Export")
        export_format = st.selectbox("Choose export format:", [
            "Plain Text (.txt)",
            "CSV (comma-separated)",
            "CSV (semicolon-separated)",
            "Google Sheets (via CSV)",
            "Apple Numbers (via CSV)"
        ])

        export_df = pd.DataFrame(preview_lines)
        output_lines = [
            "\t".join(ensure_length(fields, 8)) for fields in preview_lines
        ]
        output_str = "\n".join(output_lines)
        timestamp = datetime.now().strftime("%Y%m%d")
        csv_comma = export_df.to_csv(index=False)
        csv_semicolon = export_df.to_csv(index=False, sep=";")

        export_filename = f"{base_filename}_processed_{timestamp}"

        if export_format == "Plain Text (.txt)":
            st.download_button(
                "📥 Download .txt",
                output_str,
                file_name=f"{export_filename}.txt",
                mime="text/plain"
            )
        elif export_format == "CSV (comma-separated)":
            st.download_button(
                "📥 Download CSV",
                csv_comma,
                file_name=f"{export_filename}.csv",
                mime="text/csv"
            )
        elif export_format == "CSV (semicolon-separated)":
            st.download_button(
                "📥 Download CSV (;)",
                csv_semicolon,
                file_name=f"{export_filename}_semicolon.csv",
                mime="text/csv"
            )
        elif export_format == "Google Sheets (via CSV)":
            st.download_button(
                "📥 Download GSheets CSV",
                csv_comma,
                file_name=f"{export_filename}_GSheets.csv",
                mime="text/csv"
            )
        elif export_format == "Apple Numbers (via CSV)":
            st.download_button(
                "📥 Download Numbers CSV",
                csv_semicolon,
                file_name=f"{export_filename}_Numbers.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
else:
    st.markdown(
        '<div style="background-color:#f1f1f1;padding:10px;border-radius:5px; color:#000;">'
        '📁 <strong>Please upload a marker .txt or Premiere XML file to begin.</strong>'
        '</div>',
        unsafe_allow_html=True
    )
