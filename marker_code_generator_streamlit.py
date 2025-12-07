import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import StringIO

# Page configuration
st.set_page_config(
    page_title="VFX ShotID Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #06b6d4 0%, #2563eb 100%);
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(6, 182, 212, 0.3);
    }
    
    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.8);
        font-size: 1rem;
        margin: 0.5rem 0 0 0;
    }
    
    /* Card styling */
    .preview-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 1rem;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
        margin-bottom: 1rem;
    }
    
    .settings-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 1rem;
        padding: 2rem;
        backdrop-filter: blur(10px);
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #06b6d4 0%, #2563eb 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 0.5rem;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(6, 182, 212, 0.4);
    }
    
    /* File uploader */
    .uploadedFile {
        background: rgba(6, 182, 212, 0.1);
        border: 2px dashed #06b6d4;
        border-radius: 0.75rem;
    }
    
    /* Dataframe styling */
    .dataframe {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 0.5rem;
    }
    
    /* Info box */
    .info-box {
        background: rgba(6, 182, 212, 0.1);
        border-left: 4px solid #06b6d4;
        padding: 1rem;
        border-radius: 0.5rem;
        color: #67e8f9;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'generated_data' not in st.session_state:
    st.session_state.generated_data = None

def parse_txt_file(file_content):
    """Parse TXT marker file"""
    lines = file_content.strip().split('\n')
    data = []
    for line in lines:
        parts = line.split('\t')
        if len(parts) >= 4:
            data.append({
                'Number': parts[0],
                'Timecode': parts[1],
                'Comment': parts[2],
                'User': parts[3]
            })
    return pd.DataFrame(data)

def parse_xml_file(file_content):
    """Parse Premiere XML marker file"""
    try:
        root = ET.fromstring(file_content)
        data = []
        for marker in root.findall('.//marker'):
            data.append({
                'Number': marker.get('id', ''),
                'Timecode': marker.get('timecode', ''),
                'Comment': marker.get('comment', ''),
                'User': marker.get('user', 'VFX_EDITOR')
            })
        return pd.DataFrame(data)
    except:
        return None

def generate_shot_ids(df, showcode, add_episode, episode_num, increments, replace_username, new_username):
    """Generate shot IDs based on parameters"""
    df_result = df.copy()
    
    for idx, row in df_result.iterrows():
        # Extract comment number if exists
        comment_parts = str(row['Comment']).split('-')
        comment_num = comment_parts[0].strip() if comment_parts else ''
        
        # Calculate shot number
        shot_number = (idx + 1) * increments
        
        # Build shot ID
        shot_id_parts = [showcode]
        if add_episode:
            shot_id_parts.append(f"E{episode_num:02d}")
        if comment_num.isdigit():
            shot_id_parts.append(f"{int(comment_num):03d}")
        shot_id_parts.append(f"{shot_number:04d}")
        
        shot_id = '_'.join(shot_id_parts)
        df_result.at[idx, 'Comment'] = f"{shot_id} VFX_EDITOR"
        
        # Replace username if requested
        if replace_username and new_username:
            df_result.at[idx, 'User'] = new_username
    
    return df_result

# Header
st.markdown("""
<div class="main-header">
    <h1>🎬 VFX ShotID Generator</h1>
    <p>Convert marker files to organized shot IDs</p>
</div>
""", unsafe_allow_html=True)

# Main content
col1, col2 = st.columns([1, 1])

# File Upload Section
with col1:
    st.markdown("### 📁 Upload Marker File")
    uploaded_file = st.file_uploader(
        "Choose a TXT or XML file",
        type=['txt', 'xml'],
        help="Upload your marker file from your editing software"
    )
    
    if uploaded_file:
        file_content = uploaded_file.read().decode('utf-8')
        
        if uploaded_file.name.endswith('.txt'):
            original_df = parse_txt_file(file_content)
        else:
            original_df = parse_xml_file(file_content)
        
        if original_df is not None and not original_df.empty:
            st.success(f"✅ File loaded successfully! Found {len(original_df)} markers")
            
            with st.expander("👀 Preview Original Data", expanded=False):
                st.dataframe(original_df, use_container_width=True, hide_index=True)

# Settings Section
with col2:
    st.markdown("### ⚙️ Settings")
    
    showcode = st.text_input(
        "🎯 SHOWCODE (max 5 chars)",
        value="ABCDE",
        max_chars=5,
        help="Enter a code to identify your show/project"
    ).upper()
    
    col_ep, col_inc = st.columns(2)
    
    with col_ep:
        add_episode = st.checkbox("📺 Add EPISODE code", value=False)
        episode_num = 1
        if add_episode:
            episode_num = st.number_input("Episode Number", min_value=1, value=1, step=1)
    
    with col_inc:
        replace_username = st.checkbox("✏️ Replace username", value=False)
        new_username = ""
        if replace_username:
            new_username = st.text_input("New Username", value="VFX_SUPERVISOR")
    
    st.markdown("---")
    
    col_inc1, col_fps1 = st.columns(2)
    
    with col_inc1:
        increments = st.number_input(
            "📊 Increments",
            min_value=1,
            value=10,
            step=1,
            help="Step size for shot numbering"
        )
    
    with col_fps1:
        timebase = st.number_input(
            "🎞️ Timebase (fps)",
            min_value=1,
            value=24,
            step=1,
            help="Frame rate for XML export"
        )

# Generate Button
st.markdown("<br>", unsafe_allow_html=True)
generate_col1, generate_col2, generate_col3 = st.columns([1, 2, 1])

with generate_col2:
    if uploaded_file and original_df is not None:
        if st.button("🚀 Generate Shot IDs", use_container_width=True):
            st.session_state.generated_data = generate_shot_ids(
                original_df,
                showcode,
                add_episode,
                episode_num,
                increments,
                replace_username,
                new_username
            )
            st.success("✨ Shot IDs generated successfully!")
    else:
        st.button("🚀 Generate Shot IDs", disabled=True, use_container_width=True)
        st.info("📤 Please upload a marker file first")

# Results Section
if st.session_state.generated_data is not None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 Results")
    
    result_col1, result_col2 = st.columns(2)
    
    with result_col1:
        st.markdown("#### ❌ Before")
        st.dataframe(original_df, use_container_width=True, hide_index=True, height=400)
    
    with result_col2:
        st.markdown("#### ✅ After")
        st.dataframe(st.session_state.generated_data, use_container_width=True, hide_index=True, height=400)
    
    # Download Section
    st.markdown("<br>", unsafe_allow_html=True)
    download_col1, download_col2, download_col3 = st.columns([1, 1, 1])
    
    with download_col2:
        # Convert to CSV
        csv = st.session_state.generated_data.to_csv(index=False, sep='\t')
        st.download_button(
            label="💾 Download as TXT",
            data=csv,
            file_name=f"{showcode}_shot_ids.txt",
            mime="text/plain",
            use_container_width=True
        )

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: rgba(255, 255, 255, 0.5); padding: 2rem;'>
    <p>VFX ShotID Generator | Streamlit Edition</p>
</div>
""", unsafe_allow_html=True)
