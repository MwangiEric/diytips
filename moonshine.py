import streamlit as st
import requests
from PIL import Image
from io import BytesIO

# ============================================================================
# CONFIGURATION & PROXIES
# ============================================================================
API_URL = "https://moon-shine.vercel.app"
CORS_PROXY = "https://cors.ericmwangi13.workers.dev/?url="

# Fallback font [2026-01-15]
ST_FONT_STYLE = "sans-serif"

def get_proxied_image(url):
    """Fetches image via your CORS proxy to prevent 403/Forbidden errors."""
    if not url: return None
    try:
        proxied_url = f"{CORS_PROXY}{url}"
        resp = requests.get(proxied_url, timeout=10)
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content)).convert("RGBA")
    except Exception as e:
        st.error(f"Handshake failed: {e}")
        return None

# ============================================================================
# APP SETUP
# ============================================================================
st.set_page_config(page_title="Gemini Studio Pro", layout="wide")
st.markdown(f"""<style> html, body {{ font-family: '{ST_FONT_STYLE}'; }} </style>""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# SIDEBAR: SEARCH & FILTERS
# ----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Studio Config")
    
    with st.expander("🔍 Search Parameters", expanded=True):
        query = st.text_input("Search Term", "lion")
        asset_type = st.selectbox("Asset Style", ["None", "animals", "graffiti", "typography", "reggae", "streetwear"])
        ext = st.selectbox("File Type", ["png", "svg", "jpg"])
    
    with st.expander("🛠️ Advanced Filters"):
        min_w = st.number_input("Min Width", value=1000)
        limit = st.slider("Result Count", 10, 50, 30)
        quality_mode = st.checkbox("High Quality Only", value=True)

    if st.button("🚀 Search Global Assets", use_container_width=True, type="primary"):
        params = {"q": query, "e": ext, "limit": limit, "quality": str(quality_mode).lower()}
        if asset_type != "None": params["t"] = asset_type
        if min_w > 0: params["w"] = min_w
        
        try:
            resp = requests.get(f"{API_URL}/api/search", params=params)
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.search_results = data.get("results", {}).get("assets", [])
                st.session_state.suggestions = data.get("suggestions", {}).get("keywords", [])
            else:
                st.error("API Error")
        except Exception as e:
            st.error(f"Connection error: {e}")

# ----------------------------------------------------------------------------
# MAIN PAGE: TABS
# ----------------------------------------------------------------------------
tab1, tab2 = st.tabs(["🖼️ Asset Discovery", "👕 Jersey Canvas"])

with tab1:
    # 1. Keywords Row (Small & Scannable)
    if "suggestions" in st.session_state:
        st.caption("✨ Related Keywords")
        sug_data = st.session_state.suggestions[:12]
        cols_sug = st.columns(len(sug_data))
        for i, sug in enumerate(sug_data):
            if cols_sug[i].button(sug["keyword"], key=f"s_{i}", use_container_width=True):
                st.toast(f"Tip: Update sidebar to '{sug['keyword']}'")

    st.divider()

    # 2. Grid Results (6 columns for smaller thumbnails)
    if "search_results" in st.session_state:
        results = st.session_state.search_results
        if not results:
            st.info("No results. Adjust filters in the sidebar.")
        else:
            cols = st.columns(6) # Increased density
            for idx, asset in enumerate(results):
                with cols[idx % 6]:
                    # Displaying fixed-height containers to keep grid tidy
                    st.image(asset.get("thumbnail_src"), use_container_width=True)
                    if st.button("Select", key=f"sel_{idx}", use_container_width=True):
                        st.session_state.selected_asset = asset.get("img_url")
                        st.toast("Graphic Selected!")

# ----------------------------------------------------------------------------
# TAB 2: JERSEY CANVAS
# ----------------------------------------------------------------------------
with tab2:
    canv_col_tools, canv_col_main = st.columns([1, 3])
    
    with canv_col_tools:
        st.subheader("Canvas Setup")
        base_product = st.selectbox("Pick Base Product", [
            "Empty Canvas", 
            "Classic T-Shirt", 
            "Streetwear Hoodie", 
            "Sports Jersey"
        ])
        
        # Default Mappings
        product_urls = {
            "Empty Canvas": "https://placehold.co/1000x1000/FFFFFF/png?text=Empty+Canvas",
            "Classic T-Shirt": "https://i.imgur.com/your_tshirt_mockup.png",
            "Streetwear Hoodie": "https://i.imgur.com/your_hoodie_mockup.png",
            "Sports Jersey": "https://i.imgur.com/your_jersey_mockup.png"
        }
        
        st.divider()
        st.write("**Active Graphic:**")
        if "selected_asset" in st.session_state:
            st.caption(st.session_state.selected_asset[:50] + "...")
        else:
            st.warning("No graphic selected from Discovery tab.")

    with canv_col_main:
        if "selected_asset" in st.session_state or base_product != "Empty Canvas":
            with st.spinner("Stitching layers..."):
                # 1. Load the Base
                base_img = get_proxied_image(product_urls.get(base_product))
                
                # 2. Load the Graphic
                if "selected_asset" in st.session_state:
                    overlay = get_proxied_image(st.session_state.selected_asset)
                    
                    if base_img and overlay:
                        # Simple compositing logic (Center Overlay)
                        # We resize overlay to fit roughly 40% of the base
                        ov_w = int(base_img.width * 0.4)
                        ratio = ov_w / float(overlay.width)
                        ov_h = int(overlay.height * ratio)
                        overlay = overlay.resize((ov_w, ov_h), Image.LANCZOS)
                        
                        # Position in center
                        pos = ((base_img.width - ov_w)//2, (base_img.height - ov_h)//2)
                        base_img.paste(overlay, pos, overlay)
                
                if base_img:
                    st.image(base_img, caption=f"Preview: {base_product}", use_container_width=True)
                    
                    # Download
                    buf = BytesIO()
                    base_img.save(buf, format="PNG")
                    st.download_button("Download Design", data=buf.getvalue(), file_name="studio_export.png")
