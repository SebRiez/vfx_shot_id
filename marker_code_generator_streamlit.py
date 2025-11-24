# VFX ShotID Generator
# by Seb Riezler – erweitert für TXT + Premiere XML Import & Export

import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime
import xml.etree.ElementTree as ET
from PIL import Image

st.markdown(
    "<h1 style='text-align: center;'>🎬 VFX ShotID Generator</h1>",
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# PNG-Bilder laden (fehlerfrei, wenn sie fehlen)
# ---------------------------------------------------------
img_paths = [
    "static/Marker_example_001.png",
    "static/Marker_example_002.png"
]

images = []
for p in img_paths:
    if os.path.exists(p):
        img = Image.open(p)
        img = img.resize((int(img.width * 0.5), int(img.height * 0.5)))
        images.append(img)
    else:
        images.append(None)
        st.warning(f"⚠️ Image not found: {p}")

# Darstellung
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div style='text-align:center; font-size:18px; font-weight:bold;'>Before</div>", unsafe_allow_html=True)
    if images[0]:
        st.image(images[0])
    else:
        st.info("No image available.")

with col2:
    st.markdown("<div style='text-align:center; font-size:18px; font-weight:bold;'>After</div>", unsafe_allow_html=True)
    if images[1]:
        st.image(images[1])
    else:
        st.info("No image available.")


# ---------------------------------------------------------
# Datei-Upload
# ---------------------------------------------------------
uploaded_file = st.file_uploader(
    "📁 Upload marker file (.txt or Premiere XML)",
    type=["txt", "xml"]
)

# ---------------------------------------------------------
# Einstellungen
# ---------------------------------------------------------
showcode = st.text_input("🎬 SHOWCODE (max 5 chars):", value="ABCDE", max_chars=5).upper()
use_episode = st.checkbox("🔢 Add EPISODE code (E01)")
episode = st.text_input("Episode (e.g. E01):", value="E01").upper() if use_episode else ""

replace_user = st.checkbox("✏️ Replace username")
user_value = st.text_input("Custom Username:", value="").strip() if replace_user else ""

step_size = st.number_input("Increments", min_value=1, value=10, step=1)
timebase = st.number_input("Timebase for XML Export (fps)", min_value=1, value=24, step=1)


# ---------------------------------------------------------
# XML-Export Funktion
# ---------------------------------------------------------
def generate_premiere_xml(preview_lines, timebase: int = 24, seq_name: str = "ShotID_Markers"):

    markers_xml = []
    max_frame = 0

    for row in preview_lines:
        row = row + [""] * (8 - len(row)) if len(row) < 8 else row

        shotid = (row[4] or "").strip()
        frame_str = (row[2] or "").strip()
        comment = (row[5] or "").strip()

        if not shotid or not frame_str.isdigit():
            continue

        frame = int(frame_str)
        max_frame = max(max_frame, frame)

        markers_xml.append(f"""
        <marker>
            <name>{shotid}</name>
            <comment>{comment}</comment>
            <in>{frame}</in>
            <out>-1</out>
        </marker>
        """)

    if max_frame == 0:
        max_frame = 100

    markers_block = "\n".join(markers_xml)

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
    <sequence id="sequence-1">
        <name>{seq_name}</name>
        <duration>{max_frame + 1}</duration>
        <rate>
            <timebase>{timebase}</timebase>
            <ntsc>FALSE</ntsc>
        </rate>
{markers_block}
        <timecode>
            <rate>
                <timebase>{timebase}</timebase>
                <ntsc>FALSE</ntsc>
            </rate>
            <string>00:00:00:00</string>
            <frame>0</frame>
            <displayformat>NDF</displayformat>
        </timecode>
    </sequence>
</xmeml>
"""
    return xml_content


# ---------------------------------------------------------
# Datei-Verarbeitung (TXT + XML)
# ---------------------------------------------------------
if uploaded_file:
    try:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        base_filename = os.path.splitext(uploaded_file.name)[0]
        original_lines = []

        # ---------------- TXT Import ----------------
        if ext == ".txt":
            content = uploaded_file.read().decode("utf-8", errors="ignore")
            for line in content.strip().split("\n"):
                fields = line.strip().split("\t")
                if any(f.strip() for f in fields):
                    original_lines.append(fields)

        # ---------------- XML Import ----------------
        elif ext == ".xml":
            raw = uploaded_file.read()
            root = ET.fromstring(raw)

            for clipitem in root.findall(".//sequence/media/video//clipitem"):
                clip_name = (clipitem.findtext("name") or "").strip()
                seq_start = (clipitem.findtext("start") or "").strip()
                seq_end = (clipitem.findtext("end") or "").strip()

                for marker in clipitem.findall("marker"):
                    m_name = (marker.findtext("name") or "").strip()
                    m_comment = (marker.findtext("comment") or "").strip()
                    m_in = (marker.findtext("in") or "").strip()
                    m_out = (marker.findtext("out") or "").strip()

                    marker_text = f"{m_name} {m_comment}".strip() if m_comment else m_name

                    original_lines.append([
                        "",           # 0 User
                        clip_name,    # 1 Clipname
                        m_in,         # 2
                        m_out,        # 3
                        marker_text,  # 4 Markertext
                        m_comment,    # 5 Comment
                        seq_start,    # 6 Seq Start
                        seq_end       # 7 Seq End
                    ])

        # ---------------------------------------------------------
        # Marker-Parsing → ShotID-Zuweisung
        # ---------------------------------------------------------
        marker_codes = []
        last = ""

        for row in original_lines:
            text = row[4].strip() if len(row) > 4 else ""
            match = re.match(r"^(\d{3})\s*-", text)
            if match:
                last = match.group(1)
                marker_codes.append(last)
            else:
                marker_codes.append(last if last else "")

        # ShotID Generierung
        grouped = {}
        labeled_codes = []

        for m in marker_codes:
            if not m:
                labeled_codes.append("")
                continue
            if m not in grouped:
                grouped[m] = step_size
            num = grouped[m]
            shotid = f"{showcode}_{episode + '_' if use_episode else ''}{m}_{str(num).zfill(4)}"
            labeled_codes.append(shotid)
            grouped[m] += step_size

        # Final Preview Lines
        preview_lines = []
        for i, row in enumerate(original_lines):
            row = row + [""] * (8 - len(row)) if len(row) < 8 else row

            if replace_user and user_value:
                row[0] = user_value

            if labeled_codes[i]:
                row[4] = labeled_codes[i]

            preview_lines.append(row)

        # ---------------------------------------------------------
        # Previews
        # ---------------------------------------------------------
        st.subheader("📄 Original Preview")
        st.dataframe(original_lines[:50])

        st.subheader("✅ Processed Preview")
        st.dataframe(preview_lines[:50])

        # ---------------------------------------------------------
        # Export
        # ---------------------------------------------------------
        st.subheader("⬇️ Export")

        export_format = st.selectbox("Choose export format:", [
            "Plain Text (.txt)",
            "CSV (comma)",
            "CSV (semicolon)",
            "Google Sheets CSV",
            "Apple Numbers CSV",
            "Premiere XML (sequence markers)"
        ])

        df = pd.DataFrame(preview_lines)
        txt = "\n".join(["\t".join(r) for r in preview_lines])
        csv_c = df.to_csv(index=False)
        csv_s = df.to_csv(index=False, sep=";")
        timestamp = datetime.now().strftime("%Y%m%d")
        export_base = f"{base_filename}_processed_{timestamp}"

        if export_format == "Plain Text (.txt)":
            st.download_button("📥 Download .txt", txt, file_name=f"{export_base}.txt")

        elif export_format == "CSV (comma)":
            st.download_button("📥 Download CSV", csv_c, file_name=f"{export_base}.csv")

        elif export_format == "CSV (semicolon)":
            st.download_button("📥 Download CSV (;)", csv_s, file_name=f"{export_base}_semicolon.csv")

        elif export_format == "Google Sheets CSV":
            st.download_button("📥 Download GSheets CSV", csv_c, file_name=f"{export_base}_GSheets.csv")

        elif export_format == "Apple Numbers CSV":
            st.download_button("📥 Download Numbers CSV", csv_s, file_name=f"{export_base}_Numbers.csv")

        elif export_format == "Premiere XML (sequence markers)":
            xml_content = generate_premiere_xml(preview_lines, timebase=timebase, seq_name=export_base)
            st.download_button(
                "📥 Download Premiere XML",
                xml_content,
                file_name=f"{export_base}_PremiereMarkers.xml",
                mime="application/xml"
            )

    except Exception as e:
        st.error(f"❌ Error: {e}")

else:
    st.info("📁 Please upload a marker .txt or Premiere XML file to begin.")
