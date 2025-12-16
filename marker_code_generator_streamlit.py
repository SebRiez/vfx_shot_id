# app.py (VFX ShotID Generator – Emerald Green Theme with Color Control)

import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime
import xml.etree.ElementTree as ET
from PIL import Image # Import hinzugefügt, falls es fehlt
from xml.sax.saxutils import escape as xml_escape

# Mappe von Farbnamen zu CSS-kompatiblen Werten (Hex oder Standardname)
COLOR_HEX_MAP = {
    'Blue': '#0074D9', 'Cyan': '#00B8D4', 'Green': '#2ECC40', 
    'Yellow': '#FFDC00', 'Red': '#FF4136', 'Orange': '#FF851B', 
    'Magenta': '#FF4136', 'Purple': '#B10DC9', 'Fuchsia': '#F012BE', 
    'Rose': '#F5B0C4', 'Sky': '#87CEEB', 'Mint': '#98FB98', 
    'Lemon': '#FFFACD', 'Sand': '#F4A460', 'Cocoa': '#6F4E37', 
    'White': '#FFFFFF', 'Black': '#000000', 
    'Denim': '#1560BD'
}

# Aktualisierte Liste der standardisierten Markerfarben (basiert auf der Map)
COLOR_OPTIONS = list(COLOR_HEX_MAP.keys())

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="VFX ShotID Generator",
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# CSS – Emerald Green Palette (EditingTools.io Style)
# ---------------------------------------------------------
st.markdown("""
<style>
    /* FARBPALETTE (Emerald Green):
     * Deep Dark Grey (Hintergrund): #1E2025 
     * Mid Dark Grey (Container): #2D2F34
     * Emerald Green (Akzent, Interaktion): #42B38F
     * Light Green (Highlight): #80ED99
     * Off-White (Text): #F0F0F0
    */

    /* Main background */
    .stApp { 
        background-color: #1E2025;
        color: #F0F0F0;
    }

    /* Begrenzung der maximalen Breite des Hauptinhalts */
    .main {
        max-width: 900px; 
        padding: 0 3rem; 
        margin-left: auto;
        margin-right: auto;
    }
    
    /* Header styling (Gradient in Emerald Green) */
    .main-header {
        background: linear-gradient(135deg, #42B38F 0%, #80ED99 100%);
        padding: 2.5rem;
        border-radius: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(66, 179, 143, 0.3);
        text-align: center;
    }
    
    .main-header h1 {
        color: #1E2025; 
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 0 4px 20px rgba(0,0,0,0.3);
        letter-spacing: -0.5px;
    }
    
    .main-header p {
        color: rgba(30, 32, 37, 0.9);
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
        font-weight: 500;
    }
    
    /* Container styling (Mid Dark Grey) */
    .glass-container {
        background: #2D2F34;
        border-radius: 1.5rem;
        border: 1px solid rgba(240, 240, 240, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        padding: 2rem;
        margin-bottom: 1.5rem;
    }
    
    /* Preview cards */
    .preview-card {
        background: #2D2F34;
        border: 1px solid rgba(66, 179, 143, 0.2);
        border-radius: 1rem;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .preview-card:empty {
        display: none !important;
    }

    .preview-card:hover {
        border-color: rgba(66, 179, 143, 0.5);
        box-shadow: 0 8px 24px rgba(66, 179, 143, 0.2);
        transform: translateY(-2px);
    }
    
    /* Section headers */
    h2, h3 {
        color: #80ED99 !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
    }
    
    /* Input fields */
    div.stTextInput input, div.stNumberInput input, div[data-baseweb="select"] {
        background: #1E2025 !important; 
        border: 1px solid rgba(128, 237, 153, 0.3) !important; 
        border-radius: 0.5rem !important;
        color: #F0F0F0 !important;
        transition: all 0.3s ease !important;
    }
    
    div.stTextInput input:focus, div.stNumberInput input:focus, div[data-baseweb="select"]:focus-within {
        border-color: #42B38F !important; 
        box-shadow: 0 0 0 3px rgba(66, 179, 143, 0.3) !important;
    }
    
    /* Buttons - Primary (Emerald Green Akzent) */
    .stButton button {
        background: #42B38F !important;
        color: #1E2025 !important;
        border-radius: 0.75rem !important;
        transition: all 0.3s ease !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        box-shadow: 0 4px 12px rgba(66, 179, 143, 0.3) !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        background: #80ED99 !important;
        box-shadow: 0 8px 24px rgba(66, 179, 143, 0.5) !important;
    }
    
    /* Download buttons (Sekundärer Akzent) */
    .stDownloadButton button {
        background: rgba(128, 237, 153, 0.15) !important; 
        color: #80ED99 !important; 
        border: 1px solid rgba(128, 237, 153, 0.3) !important;
        border-radius: 0.75rem !important;
        transition: all 0.3s ease !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
    }
    
    .stDownloadButton button:hover {
        background: rgba(128, 237, 153, 0.25) !important;
        border-color: #42B38F !important; 
        transform: translateY(-2px) !important;
    }
    
    /* File uploader (Dunkler Hintergrund mit hellem Rand) */
    div[data-testid="stFileUploader"] {
        background: #2D2F34;
        border: 2px dashed rgba(128, 237, 153, 0.5); 
        border-radius: 1rem;
        padding: 2rem;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stFileUploader"]:hover {
        border-color: #42B38F;
        background: rgba(66, 179, 143, 0.1);
    }
    
    /* Bilder: Skalierung und Zentrierung */
    div[data-testid="stImage"] img {
        border-radius: 1rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(240, 240, 240, 0.1);
        max-width: 50%; 
        height: auto;
        display: block; 
        margin-left: auto; 
        margin-right: auto; 
    }
    
    /* Dataframes */
    .dataframe {
        background: #2D2F34 !important;
        border-radius: 0.75rem !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: #2D2F34;
        padding: 0.5rem;
        border-radius: 0.75rem;
    }
    
    .stTabs [aria-selected="true"] {
        /* Aktiver Tab als heller Akzent */
        background: linear-gradient(135deg, #42B38F 0%, #80ED99 100%);
        color: #1E2025 !important; 
    }
    
    /* Info/Success/Error */
    .stAlert {
        border-left: 4px solid #42B38F;
        color: #80ED99;
    }
    div[data-testid="stSuccess"] {
        border-left: 4px solid #4CAF50 !important;
        color: #4CAF50 !important;
    }
    div[data-testid="stError"] {
        border-left: 4px solid #F44336 !important;
        color: #F44336 !important;
    }
    
    /* Divider */
    hr {
        border-color: rgba(240, 240, 240, 0.1) !important;
        margin: 2rem 0 !important;
    }
    
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Load optional PNG preview images (REINTEGRIERT)
# ---------------------------------------------------------
img_paths = ["static/Marker_example_001.png", "static/Marker_example_002.png"]
images = []
for p in img_paths:
    if os.path.exists(p):
        try:
            img = Image.open(p)
            images.append(img)
        except Exception:
            images.append(None)
    else:
        images.append(None)

# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>VFX ShotID Generator</h1>
    <p>Convert marker files to organized shot IDs with professional precision</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Preview Section (REINTEGRIERT mit If-Else-Logik)
# ---------------------------------------------------------
st.markdown('<div class="glass-container">', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="preview-card">', unsafe_allow_html=True)
    st.markdown("### ❌ Before")
    # Bild oder Info anzeigen
    if images and images[0] is not None:
        st.image(images[0], use_column_width=False)
    else:
        st.info("Preview image not found (static/Marker_example_001.png)")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="preview-card">', unsafe_allow_html=True)
    st.markdown("### ✅ After")
    # Bild oder Info anzeigen
    if images and images[1] is not None:
        st.image(images[1], use_column_width=False)
    else:
        st.info("Preview image not found (static/Marker_example_002.png)")
    st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# Upload Section
# ---------------------------------------------------------
st.markdown('<div class="glass-container">', unsafe_allow_html=True)
st.markdown("### 📁 Upload Marker File")
uploaded_file = st.file_uploader(
    "Choose an Avid TXT or PremierePro XML file",
    type=["txt", "xml"],
    help="Upload your marker file from your editing software"
)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# Settings Section
# ---------------------------------------------------------
st.markdown('<div class="glass-container">', unsafe_allow_html=True)
st.markdown("### ⚙️ Settings")

# Dictionary der Frame-Raten
fps_options = {
    "23.98 fps (23.976)": 23.976, "24 fps": 24, "25 fps": 25, 
    "29.97 fps (Drop Frame)": 29.97, "30 fps": 30, "60 fps": 60
}

# --- SHOTID & USER SETTINGS ---
colA, colB = st.columns(2)
with colA:
    showcode = st.text_input("🎯 SHOWCODE (max 5 chars):", value="ABCDE", max_chars=5).upper()
with colB:
    step_size = st.number_input("📊 Increments (Step Size):", min_value=1, value=10, step=1)

colC, colD = st.columns(2)
with colC:
    use_episode = st.checkbox("📺 Add EPISODE code (E01)")
    episode = st.text_input("Episode (e.g. E01):", value="E01").upper() if use_episode else ""
with colD:
    replace_user = st.checkbox("✏️ Replace username in column 1")
    user_value = st.text_input("Custom Username:", value="VFX_ARTIST").strip() if replace_user else ""

# --- FPS & MARKER TYPE SETTINGS ---
colE, colF = st.columns(2)
with colE:
    selected_fps_label = st.selectbox(
        "🎞️ Timebase for XML Export (fps)", 
        options=list(fps_options.keys()),
        index=1
    )
    timebase = fps_options[selected_fps_label]
with colF:
    marker_type = st.selectbox(
        "📍 XML Marker Type",
        options=["Clip Markers (Standard)", "Sequence Markers"],
        index=0,
        help="Clip Markers: Markiert den Clip. Sequence Markers: Markiert die Zeitleiste."
    )

st.markdown("---")
st.markdown("### 🌈 Marker Color Settings")

# --- HELPER FUNKTION FÜR FARBAUSWAHL MIT SWATCH ---
def get_swatch_html(color_name: str, size: int = 15) -> str:
    """Erzeugt den HTML-Code für einen Farbkreis (Swatch)."""
    hex_code = COLOR_HEX_MAP.get(color_name, '#FFFFFF')
    # Dünner, dunkler Rand für bessere Sichtbarkeit von hellen Farben (Lemon, White)
    border_style = '1px solid rgba(0, 0, 0, 0.5)' if color_name in ["White", "Lemon"] else '1px solid rgba(255, 255, 255, 0.2)'
    return f'<span style="display: inline-block; width: {size}px; height: {size}px; border-radius: 50%; background-color: {hex_code}; border: {border_style}; margin-right: 8px; vertical-align: middle;"></span>'

# Workaround: Checkbox-Status im Session State speichern, um die visuelle Reihenfolge zu tauschen
if "override_enable_key" not in st.session_state:
    st.session_state["override_enable_key"] = False

colG, colH = st.columns(2)
with colG:
    # 1. Standardfarbe für leere Einträge
    default_color = st.selectbox(
        "🎨 Default Color (for empty input)",
        options=COLOR_OPTIONS,
        index=COLOR_OPTIONS.index("Green"), # Default ist Green
        help="Color to use if the input file does not specify a marker color.",
        key="default_color",
    )

with colH:
    # 2. Optionale Farb-Override: Selectbox zuerst anzeigen
    override_color = st.selectbox(
        "Forced Export Color",
        options=COLOR_OPTIONS,
        index=COLOR_OPTIONS.index("Denim"),
        # Disabled-Status wird vom Session State der Checkbox gesteuert
        disabled=not st.session_state["override_enable_key"], 
        key="override_color",
    )
    
    # Checkbox DANACH anzeigen (visuell unterhalb der Selectbox)
    override_color_enable = st.checkbox(
        "🔥 Force All Markers to One Color", 
        key="override_enable_key", # Greift auf den Session State zu und aktualisiert ihn
    )


# --- VISUELLE BESTÄTIGUNG DER GEWÄHLTEN FARBEN ---
st.markdown('<br>', unsafe_allow_html=True)
st.markdown(f"**Default Color:** {get_swatch_html(default_color)}{default_color}", unsafe_allow_html=True)
if st.session_state["override_enable_key"]: # Verwende den aktuellen Zustand der Checkbox
    st.markdown(f"**Forced Color:** {get_swatch_html(override_color)}{override_color}", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# Helper: Timecode → Frames (Unchanged)
# ---------------------------------------------------------
def timecode_to_frames(tc: str, fps: float):
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
    
    total_seconds = (h * 3600) + (m * 60) + s
    # Rundung, um float-Fehler bei der Frame-Berechnung zu vermeiden
    return int(round(total_seconds * fps + f))

# ---------------------------------------------------------
# XML-Export: Clip-Marker ODER Sequence-Marker (Unchanged)
# ---------------------------------------------------------
def generate_premiere_xml(preview_lines, fps: float, seq_name: str, marker_type: str):
    marker_xml_chunks = []
    max_frame = 0
    fps_float = float(fps)
    
    timebase_int = round(fps_float) 

    # Marker-Daten sammeln
    for row in preview_lines:
        row = row + [""] * (8 - len(row)) if len(row) < 8 else row
        tc_str   = (row[1] or "").strip()
        col2     = (row[2] or "").strip()
        color    = (row[3] or "Cyan").strip() # Wichtig: Nimmt die bereits korrigierte Farbe
        shotid   = (row[4] or "").strip()
        col5     = (row[5] or "").strip()

        if not shotid:
            continue

        if col2.isdigit():
            frame_in = int(col2)
        else:
            frame_in = timecode_to_frames(tc_str, fps_float)

        if frame_in is None:
            continue

        dur = int(col5) if col5.isdigit() and int(col5) > 0 else 1
        frame_out = frame_in + dur
        max_frame = max(max_frame, frame_out)

        comment = col5 if col5 and not col5.isdigit() else shotid

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

    duration = max_frame + 1 if marker_xml_chunks else 100
    duration_str = str(duration)
    
    markers_block = "\n".join(marker_xml_chunks)
    
    sequence_markers = markers_block if marker_type == "Sequence Markers" else ""
    clip_markers = markers_block if marker_type == "Clip Markers (Standard)" else ""

    
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
  <sequence id="sequence-1">
    <name>{xml_escape(seq_name)}</name>
    <duration>{duration_str}</duration>
    <rate>
      <timebase>{timebase_int}</timebase>
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
              <timebase>{timebase_int}</timebase>
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
                <timebase>{timebase_int}</timebase>
                <ntsc>FALSE</ntsc>
              </rate>
            </file>
{clip_markers}  </clipitem>
        </track>
      </video>
    </media>
    <timecode>
      <rate>
        <timebase>{timebase_int}</timebase>
        <ntsc>FALSE</ntsc>
      </rate>
      <string>00:00:00:00</string>
      <frame>0</frame>
      <displayformat>NDF</displayformat>
    </timecode>
{sequence_markers} </sequence>
</xmeml>
"""
    return xml_content

# ---------------------------------------------------------
# MAIN PROCESSING
# ---------------------------------------------------------
if uploaded_file:
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    
    try:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        base_filename = os.path.splitext(uploaded_file.name)[0]
        original_lines = []

        # --- IMPORT LOGIC (Unchanged) ---
        if ext == ".txt":
            content = uploaded_file.read().decode("utf-8", errors="ignore")
            for line in content.split("\n"):
                f = line.strip().split("\t")
                if any(v.strip() for v in f):
                    original_lines.append(f)

        elif ext == ".xml":
            raw = uploaded_file.read()
            root = ET.fromstring(raw)
            for marker in root.findall(".//marker"):
                name = marker.findtext("name") or ""
                comment = marker.findtext("comment") or ""
                frame_in = marker.findtext("in") or "0"
                
                # Farbwert aus XML auslesen (falls vorhanden, sonst leer)
                xml_color = marker.findtext("color") or "" 
                
                original_lines.append([
                    "", "", frame_in, xml_color, # Wichtig: XML Farbe wird hier eingefügt
                    name, comment, "", ""
                ])

        # --- SHOTID ASSIGNMENT (Unchanged) ---
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

        for i, g in enumerate(marker_group):
            if not g:
                labeled.append(original_lines[i][4] if len(original_lines[i]) > 4 else "")
                continue
            
            if g not in group_counter:
                group_counter[g] = step_size
                
            num = group_counter[g]
            ep = f"{episode}_" if episode else ""
            shotid = f"{showcode}_{ep}{g}_{str(num).zfill(4)}"
            labeled.append(shotid)
            group_counter[g] += step_size

        # --- FINAL PREVIEW LINE ASSEMBLY (Color Logic) ---
        preview_lines = []
        # Den Wert aus dem Session State lesen, da die Checkbox später definiert wurde
        override_active = st.session_state.get("override_enable_key", False) 
        
        for i, row in enumerate(original_lines):
            # Sicherstellen, dass die Zeile mindestens 8 Spalten hat
            row = row + [""] * (8 - len(row)) if len(row) < 8 else row
            
            # 1. Farbe bestimmen (Spalte 3)
            input_color = (row[3] or "").strip()
            final_color = default_color # Startwert: Vom Nutzer definierte Standardfarbe

            if override_active:
                # Override ist aktiv: Erzwinge die gewählte Override-Farbe
                final_color = override_color
            elif input_color:
                # Override ist inaktiv: Wenn die Eingabefarbe gültig ist, übernehme sie
                if input_color in COLOR_OPTIONS:
                    final_color = input_color
                # Wenn die Eingabefarbe ungültig ist, bleibt es bei der 'default_color'

            # 2. Werte zuweisen
            row[3] = final_color # Wende die finale Farbe an
            
            if replace_user and user_value:
                row[0] = user_value
            if labeled[i]:
                row[4] = labeled[i]
            
            preview_lines.append(row)


# ... (nach der Preview-Schleife)

            st.markdown("---")
            st.markdown("### ⬇️ Export Settings & Download")

            # --- DATEINAME ABFRAGE ---
            timestamp = datetime.now().strftime("%Y%m%d")
            default_export_name = f"{base_filename}_processed_{timestamp}"
            
            # Das Textfeld erlaubt dem User, den Namen anzupassen
            custom_export_name = st.text_input(
                "📁 Filename for Export (without extension):", 
                value=default_export_name,
                help="The extension (.txt, .xml, etc.) will be added automatically."
            ).strip()

            # Fallback falls der User das Feld komplett leert
            final_filename = custom_export_name if custom_export_name else default_export_name

            # Daten für den Download generieren
            df = pd.DataFrame(preview_lines)
            txt = "\n".join(["\t".join(r) for r in preview_lines])
            csv_c = df.to_csv(index=False)
            csv_s = df.to_csv(index=False, sep=";")

            # XML-Exporte generieren (verwenden nun den gewählten Namen intern in der XML)
            premiere_xml_content = generate_premiere_xml(preview_lines, fps=timebase, seq_name=final_filename, marker_type=marker_type)
            avid_xml_content = generate_avid_xml(preview_lines, seq_name=final_filename)

            # Download Buttons mit dem dynamischen Namen
            col_dl1, col_dl2, col_dl3, col_dl4, col_dl5 = st.columns(5) 

            with col_dl1:
                st.download_button("📥 TXT", txt, file_name=f"{final_filename}.txt", use_container_width=True)

            with col_dl2:
                st.download_button("📥 CSV (,)", csv_c, file_name=f"{final_filename}_comma.csv", use_container_width=True)

            with col_dl3:
                st.download_button("📥 CSV (;)", csv_s, file_name=f"{final_filename}_semicolon.csv", use_container_width=True)

            with col_dl4:
                st.download_button(
                    "📥 Premiere XML",
                    premiere_xml_content,
                    file_name=f"{final_filename}_Premiere.xml",
                    mime="application/xml",
                    use_container_width=True
                )
            
            with col_dl5:
                 st.download_button(
                    "📥 Avid XML",
                    avid_xml_content,
                    file_name=f"{final_filename}_Avid.xml",
                    mime="application/xml",
                    use_container_width=True
                )

        st.success("✅ Processing complete! Download your files above.")
        

    except Exception as e:
        st.error(f"❌ Processing Error: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown('<div class="glass-container">', unsafe_allow_html=True)
    st.info("📤 Please upload an Avid marker .txt or Premiere XML file to begin processing.")
    st.markdown('</div>', unsafe_allow_html=True)
