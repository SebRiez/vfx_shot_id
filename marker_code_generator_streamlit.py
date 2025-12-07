# app.py (VFX ShotID Generator – modern UI + Premiere Clip-Marker XML)

import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime
import xml.etree.ElementTree as ET
from PIL import Image
from xml.sax.saxutils import escape as xml_escape

# ---------------------------------------------------------
# CSS – Dark Mode + Glass Morphism Style
# ---------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0b1121; color: #ffffff; }
    .glass-container {
        background: rgba(30,41,59,0.5);
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 4px 30px rgba(0,0,0,0.4);
        backdrop-filter: blur(8px);
        padding: 30px;
        margin-bottom: 20px;
    }
    h1 {
        color:#8be9fd;
        text-shadow:0 0 5px rgba(139,233,253,0.5);
        text-align:center;
    }
    div.stTextInput input, div.stNumberInput input {
        background-color: rgba(45,62,80,0.8)!important;
        border:1px solid #4a5568!important;
        color:white!important;
    }
    .stButton button, .stDownloadButton button {
        background:#6272a4;
        color:white;
        border-radius:8px;
        transition:0.2s;
        border:none;
    }
    .stButton button:hover, .stDownloadButton button:hover {
        background:#8be9fd;
        color:#0b1121;
    }
    div[data-testid="stImage"] img {
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Load optional PNG preview images
# ---------------------------------------------------------
img_paths = ["static/Marker_example_001.png", "static/Marker_example_002.png"]
images = []
for p in img_paths:
    if os.path.exists(p):
        try:
            img = Image.open(p)
            img = img.resize((int(img.width * 0.5), int(img.height * 0.5)))
            images.append(img)
        except Exception:
            images.append(None)
    else:
        images.append(None)

# ---------------------------------------------------------
# Main container
# ---------------------------------------------------------
st.markdown('<div class="glass-container">', unsafe_allow_html=True)
st.markdown("<h1>🎬 VFX ShotID Generator</h1>", unsafe_allow_html=True)

# Preview images
col1, col2 = st.columns(2)
with col1:
    st.write("### Before")
    if images[0] is not None:
        st.image(images[0])
    else:
        st.info("No image.")
with col2:
    st.write("### After")
    if images[1] is not None:
        st.image(images[1])
    else:
        st.info("No image.")

st.markdown("---")

# ---------------------------------------------------------
# Upload
# ---------------------------------------------------------
uploaded_file = st.file_uploader("📁 Upload Marker File (.txt or .xml)", type=["txt", "xml"])

# ---------------------------------------------------------
# Settings
# ---------------------------------------------------------
st.subheader("⚙ Settings")

colA, colB = st.columns(2)
with colA:
    showcode = st.text_input("SHOWCODE (max 5 chars):", value="ABCDE", max_chars=5).upper()
with colB:
    step_size = st.number_input("Increments (Step Size):", min_value=1, value=10, step=1)

colC, colD = st.columns(2)
with colC:
    use_episode = st.checkbox("Add EPISODE code (E01)")
    episode = st.text_input("Episode (e.g. E01):", value="E01").upper() if use_episode else ""

with colD:
    replace_user = st.checkbox("Replace username in column 1")
    user_value = st.text_input("Custom Username:", value="VFX_ARTIST").strip() if replace_user else ""

timebase = st.number_input("Timebase for XML Export (fps)", min_value=1, value=24, step=1)

# ---------------------------------------------------------
# Helper: Timecode → Frames
# ---------------------------------------------------------
def timecode_to_frames(tc: str, fps: int):
    """
    Konvertiert 'HH:MM:SS:FF' nach Frames.
    """
    if not tc or ":" not in tc:
        return None
    parts = tc.strip().split(":")
    if len(parts) != 4:
        return None
    try:
        h = int(parts[0])
        m = int(parts[1])
        s = int(parts[2])
        f = int(parts[3])
    except ValueError:
        return None
    return ((h * 3600) + (m * 60) + s) * fps + f

# ---------------------------------------------------------
# XML-Export: Clip-Marker (Variante B)
# ---------------------------------------------------------
def generate_premiere_xml(preview_lines, fps: int = 24, seq_name: str = "ShotID_Markers"):
    """
    Erstellt ein FCP-XML (xmeml), das von Premiere als Sequenz mit
    EINEM Clipitem und darin liegenden Markern importiert werden kann.

    Erwartete Struktur von preview_lines (pro Zeile):
        [0]  optional: Username
        [1]  Timecode (z.B. 01:01:06:10) ODER leer
        [2]  Frameposition (wenn XML-Import) ODER Track/sonstiges
        [3]  Marker-Farbe (z.B. Cyan)
        [4]  ShotID (Marker-Name)
        [5]  Kommentar oder Dauer (wenn Zahl)
        [6]  optional
        [7]  optional
    """

    marker_xml_chunks = []
    max_frame = 0
    fps_int = int(fps)

    for row in preview_lines:
        # auf mind. 8 Felder auffüllen
        row = row + [""] * (8 - len(row)) if len(row) < 8 else row

        username = (row[0] or "").strip()
        tc_str   = (row[1] or "").strip()
        col2     = (row[2] or "").strip()
        color    = (row[3] or "Cyan").strip()
        shotid   = (row[4] or "").strip()
        col5     = (row[5] or "").strip()

        if not shotid:
            continue

        # IN-Frame bestimmen
        if col2.isdigit():
            # XML-Import: Spalte 2 enthält Frameposition
            frame_in = int(col2)
        else:
            # TXT-Import: Spalte 1 enthält Timecode
            frame_in = timecode_to_frames(tc_str, fps_int)

        if frame_in is None:
            continue

        # Dauer: wenn Spalte 5 eine Zahl ist, als Frames nutzen, sonst 1 Frame
        if col5.isdigit():
            dur = int(col5)
            if dur <= 0:
                dur = 1
        else:
            dur = 1

        frame_out = frame_in + dur
        max_frame = max(max_frame, frame_out)

        # Kommentar: wenn col5 kein reiner Zahlenwert → als Kommentar, sonst ShotID
        if col5 and not col5.isdigit():
            comment = col5
        else:
            comment = shotid

        name_xml    = xml_escape(shotid)
        comment_xml = xml_escape(comment)
        color_xml   = xml_escape(color)

        marker_xml_chunks.append(f"""
                <marker>
                    <name>{name_xml}</name>
                    <comment>{comment_xml}</comment>
                    <in>{frame_in}</in>
                    <out>{frame_out}</out>
                    <color>{color_xml}</color>
                </marker>""")

    if not marker_xml_chunks:
        duration = 100
    else:
        duration = max_frame + 1

    duration_str = str(duration)
    fps_str = str(fps_int)
    markers_block = "\n".join(marker_xml_chunks)

    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
  <sequence id="sequence-1">
    <name>{xml_escape(seq_name)}</name>
    <duration>{duration_str}</duration>
    <rate>
      <timebase>{fps_str}</timebase>
      <ntsc>FALSE</ntsc>
    </rate>
    <media>
      <video>
        <track>
          <clipitem id="clipitem-1">
            <name>{xml_escape(seq_name)}</name>
            <enabled>TRUE</enabled>
            <duration>{duration_str}</duration>
            <rate>
              <timebase>{fps_str}</timebase>
              <ntsc>FALSE</ntsc>
            </rate>
            <start>0</start>
            <end>{duration_str}</end>
            <in>0</in>
            <out>{duration_str}</out>
            <file id="file-1">
              <name>{xml_escape(seq_name)}</name>
              <duration>{duration_str}</duration>
              <rate>
                <timebase>{fps_str}</timebase>
                <ntsc>FALSE</ntsc>
              </rate>
            </file>
{markers_block}
          </clipitem>
        </track>
      </video>
    </media>
    <timecode>
      <rate>
        <timebase>{fps_str}</timebase>
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
# MAIN PROCESSING
# ---------------------------------------------------------
if uploaded_file:
    try:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        base_filename = os.path.splitext(uploaded_file.name)[0]
        original_lines = []

        # ------------------------ TXT IMPORT ------------------------
        if ext == ".txt":
            content = uploaded_file.read().decode("utf-8", errors="ignore")
            for line in content.split("\n"):
                f = line.strip().split("\t")
                if any(v.strip() for v in f):
                    original_lines.append(f)

        # ------------------------ XML IMPORT ------------------------
        elif ext == ".xml":
            raw = uploaded_file.read()
            root = ET.fromstring(raw)

            # generische Marker-Extraktion aus bestehendem FCP-XML / Premiere-XML
            for marker in root.findall(".//marker"):
                name = marker.findtext("name") or ""
                comment = marker.findtext("comment") or ""
                frame_in = marker.findtext("in") or "0"
                frame_out = marker.findtext("out") or "0"

                original_lines.append([
                    "",         # username placeholder
                    "",         # kein TC → nur Frames
                    frame_in,   # IN-frame
                    "Cyan",     # default color
                    name,
                    comment,
                    "", ""
                ])

        # ---------------------- SHOTID ASSIGNMENT -------------------
        marker_group = []
        current_group = ""

        for row in original_lines:
            text = row[4].strip() if len(row) > 4 else ""
            m = re.match(r"^(\d{3})\s*-", text)
            if m:
                current_group = m.group(1)
            marker_group.append(current_group)

        group_counter = {}
        labeled = []

        for g in marker_group:
            if not g:
                labeled.append("")
                continue
            if g not in group_counter:
                group_counter[g] = step_size
            num = group_counter[g]
            ep = f"{episode}_" if episode else ""
            shotid = f"{showcode}_{ep}{g}_{str(num).zfill(4)}"
            labeled.append(shotid)
            group_counter[g] += step_size

        preview_lines = []
        for i, row in enumerate(original_lines):
            row = row + [""] * (8 - len(row)) if len(row) < 8 else row
            if replace_user and user_value:
                row[0] = user_value
            if labeled[i]:
                row[4] = labeled[i]
            preview_lines.append(row)

        # ---------------------------------------------------------
        # PREVIEW + EXPORT
        # ---------------------------------------------------------
        st.subheader("📊 Data Preview")
        tab1, tab2 = st.tabs(["Original Data", "Processed Data"])
        with tab1:
            st.dataframe(original_lines)
        with tab2:
            st.dataframe(preview_lines)

        st.markdown("---")
        st.subheader("⬇️ Export")

        df = pd.DataFrame(preview_lines)
        txt = "\n".join(["\t".join(r) for r in preview_lines])
        csv_c = df.to_csv(index=False)
        csv_s = df.to_csv(index=False, sep=";")

        timestamp = datetime.now().strftime("%Y%m%d")
        export_base = f"{base_filename}_processed_{timestamp}"

        col_dl1, col_dl2, col_dl3, col_dl4 = st.columns(4)

        with col_dl1:
            st.download_button("📥 TXT", txt, file_name=f"{export_base}.txt")

        with col_dl2:
            st.download_button("📥 CSV (,)", csv_c, file_name=f"{export_base}_comma.csv")

        with col_dl3:
            st.download_button("📥 CSV (;)", csv_s, file_name=f"{export_base}_semicolon.csv")

        with col_dl4:
            xml_content = generate_premiere_xml(preview_lines, fps=timebase, seq_name=export_base)
            st.download_button(
                "📥 Premiere XML",
                xml_content,
                file_name=f"{export_base}_PremiereMarkers.xml",
                mime="application/xml"
            )

    except Exception as e:
        st.error(f"❌ Processing Error: {e}")

else:
    st.info("📁 Please upload a marker .txt or Premiere XML file to begin.")

st.markdown('</div>', unsafe_allow_html=True)
