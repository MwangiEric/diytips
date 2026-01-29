import streamlit as st
import requests
from PIL import Image
from io import BytesIO

# ============================================================================
# CONFIGURATION
# ============================================================================
API_URL = "https://moon-shine.vercel.app"  # Update this to your deployed API URL
DEFAULT_JERSEY = "https://i.imgur.com/your_jersey_template.png" 

# Fallback font setting per your instructions [2026-01-15]
ST_FONT_STYLE = "sans-serif"

def get_pil_image(url):
    """Fetch image from URL and convert to RGBA for transparency support."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content)).convert("RGBA")
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return None

# ============================================================================
# APP INTERFACE
# ============================================================================
st.set_page_config(page_title="Gemini Studio", layout="wide")

# Apply fallback font styling via CSS
st.markdown(f"""<style> html, body, [class*="css"] {{ font-family: '{ST_FONT_STYLE}'; }} </style>""", unsafe_allow_html=True)

st.title("🎨 Gemini Asset & Jersey Studio")

# Sidebar for Global Filters
with st.sidebar:
    st.header("Search Filters")
    min_w = st.number_input("Min Width (px)", value=1000, step=500)
    limit = st.slider("Results Limit", 1, 50, 20)
    quality_mode = st.checkbox("Quality Filter (No Watermarks)", value=True)
    
    st.divider()
    st.info("Debug Info")
    if "last_query" in st.session_state:
        st.code(st.session_state.last_query)

tab1, tab2 = st.tabs(["🔍 Discovery", "👕 Jersey Canvas"])

# ----------------------------------------------------------------------------
# TAB 1: DISCOVERY (SEARCH)
# ----------------------------------------------------------------------------
with tab1:
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        query = st.text_input("What are you looking for?", placeholder="e.g. vintage lion, cyberpunk car")
    with col2:
        # These match your FastAPI AssetType Enum
        asset_type = st.selectbox("Style", ["None", "animals", "graffiti", "typography", "retro", "anime", "streetwear"])
    with col3:
        ext = st.selectbox("Format", ["png", "jpg", "svg"])

    if st.button("Find Assets", type="primary", use_container_width=True):
        # Build Params
        params = {"q": query, "e": ext, "limit": limit, "quality": str(quality_mode).lower()}
        if asset_type != "None": params["t"] = asset_type
        if min_w > 0: params["w"] = min_w
        
        st.session_state.last_query = f"{API_URL}/api/search?q={query}..."
        
        with st.spinner("Searching global databases..."):
            try:
                resp = requests.get(f"{API_URL}/api/search", params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    # ACCESS NESTED RESULTS: results -> assets
                    st.session_state.search_results = data.get("results", {}).get("assets", [])
                    st.session_state.suggestions = data.get("suggestions", {}).get("keywords", [])
                else:
                    st.error(f"API Error {resp.status_code}: {resp.text}")
            except Exception as e:
                st.error(f"Connection Failed: {e}")

    # Keyword Suggestions Bar
    if "suggestions" in st.session_state and st.session_state.suggestions:
        st.write("✨ **Related Keywords:**")
        sug_cols = st.columns(len(st.session_state.suggestions[:6]))
        for i, sug in enumerate(st.session_state.suggestions[:6]):
            if sug_cols[i].button(sug["keyword"], key=f"sug_{i}", use_container_width=True):
                st.toast(f"Tip: Try searching for '{sug['keyword']}'")

    st.divider()

    # Results Grid
    if "search_results" in st.session_state:
        if not st.session_state.search_results:
            st.warning("No assets found. Try lowering the Min Width or changing keywords.")
        else:
            cols = st.columns(4)
            for idx, asset in enumerate(st.session_state.search_results):
                with cols[idx % 4]:
                    # Use thumbnail_src for the grid view
                    st.image(asset.get("thumbnail_src"), use_container_width=True)
                    st.caption(f"📍 {asset.get('source_site')} | {asset.get('resolution')}")
                    
                    if st.button("Select High-Res", key=f"btn_{idx}", use_container_width=True):
                        st.session_state.selected_img_url = asset.get("img_url")
                        st.success("Loaded to Canvas!")

# ----------------------------------------------------------------------------
# TAB 2: JERSEY CANVAS (RENDERING)
# ----------------------------------------------------------------------------
with tab2:
    if "selected_img_url" not in st.session_state:
        st.info("Please select a graphic from the Discovery tab first.")
    else:
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.subheader("Placement Controls")
            # In a real app, you'd add sliders for X/Y position and scale here
            st.write("**Current Graphic URL:**")
            st.code(st.session_state.selected_img_url)
            
            if st.button("🔄 Reset Canvas"):
                del st.session_state.selected_img_url
                st.rerun()

        with c2:
            st.subheader("Preview")
            with st.spinner("Rendering High-Res Preview..."):
                graphic = get_pil_image(st.session_state.selected_img_url)
                if graphic:
                    st.image(graphic, caption="High-Resolution Source", use_container_width=True)
                    st.download_button("Download PNG", data=requests.get(st.session_state.selected_img_url).content, file_name="gemini_asset.png")
