import streamlit as st
import requests
import base64
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# ============================================================================
# 1. CONFIGURATION & URLS
# ============================================================================
API_URL = "https://moon-shine.vercel.app"
CORS_PROXY = "https://cors.ericmwangi13.workers.dev/?url="
BASE_SIZE = 2000 

# Mockups provided by user
MOCKUPS = {
    "Empty Canvas": "https://placehold.co/2000x2000/FFFFFF/png?text=+",
    "Premium Black Shirt": "https://ik.imagekit.io/ericmwangi/_Pngtree_premium%20black%20t%20shirt%20mockup_18848206.png",
    "Standard Black Shirt": "https://ik.imagekit.io/ericmwangi/tshtblck.png",
    "Realistic White Shirt": "https://ik.imagekit.io/ericmwangi/_Pngtree_realistic%20white%20t%20shirt%20vector_8963503.png"
}

# Fallback font [2026-01-15]
ST_FONT_STYLE = "sans-serif"

# ============================================================================
# 2. CORE UTILITIES
# ============================================================================
def get_img(input_data):
    """Universal loader: Fixes // protocols, handles Base64, and uses CORS proxy."""
    if not input_data: return None
    try:
        # A. Base64 Logic
        if isinstance(input_data, str) and input_data.startswith("data:image"):
            _, encoded = input_data.split(",", 1)
            return Image.open(BytesIO(base64.b64decode(encoded))).convert("RGBA")
        
        # B. URL Logic & Protocol Fix (// to https://)
        url = str(input_data)
        if url.startswith("//"):
            url = "https:" + url
            
        # C. Proxy & Fetch
        target = f"{CORS_PROXY}{url}" if "http" in url and CORS_PROXY not in url else url
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(target, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            return Image.open(BytesIO(resp.content)).convert("RGBA")
        return None
    except:
        return None

# ============================================================================
# 3. INTERFACE & SIDEBAR
# ============================================================================
st.set_page_config(page_title="Gemini Studio Pro", layout="wide")

with st.sidebar:
    st.title("⚙️ Studio Controls")
    q_input = st.text_input("Keywords", "Lion")
    t_input = st.selectbox("Style Category", ["None", "animals", "graffiti", "typography", "reggae", "streetwear"])
    
    if st.button("🔍 Find Assets", use_container_width=True, type="primary"):
        params = {"q": q_input, "limit": 36} # More results for the grid
        if t_input != "None": params["t"] = t_input
        try:
            r = requests.get(f"{API_URL}/api/search", params=params)
            if r.status_code == 200:
                data = r.json()
                st.session_state.results = data.get("results", {}).get("assets", [])
                st.session_state.chips = data.get("suggestions", {}).get("keywords", [])
        except:
            st.error("Search API is currently unavailable.")

    # SIDEBAR: Keyword Chips
    if "chips" in st.session_state and st.session_state.chips:
        st.divider()
        st.subheader("✨ Keyword Suggestions")
        for sug in st.session_state.chips[:12]:
            if st.button(f"#{sug['keyword']}", key=f"s_{sug['keyword']}", use_container_width=True):
                st.toast(f"Try searching: {sug['keyword']}")

# ============================================================================
# 4. MAIN TABS
# ============================================================================
tab_discovery, tab_canvas = st.tabs(["🖼️ Asset Discovery", "👕 Design Canvas"])

# --- DISCOVERY TAB ---
with tab_discovery:
    if "results" in st.session_state:
        cols = st.columns(6)
        for idx, item in enumerate(st.session_state.results):
            with cols[idx % 6]:
                # Fix Protocol for display
                t_url = item.get("thumbnail_src", "")
                if t_url.startswith("//"): t_url = "https:" + t_url
                
                st.image(t_url, use_container_width=True)
                
                # Double Action Buttons
                c1, c2 = st.columns(2)
                if c1.button("➕", key=f"sel_{idx}", help="Select for Canvas"):
                    st.session_state.active_graphic = item.get("img_url")
                    st.toast("Loaded to Canvas!")
                
                d_url = item.get("img_url", "")
                if d_url.startswith("//"): d_url = "https:" + d_url
                c2.download_button("💾", data=d_url, key=f"dl_{idx}", help="Download Separately")

# --- CANVAS TAB ---
with tab_canvas:
    tool_col, view_col = st.columns([1, 2.5])
    
    with tool_col:
        st.subheader("1. Template")
        base_choice = st.selectbox("Mockup Base", list(MOCKUPS.keys()), index=0)
        
        st.divider()
        st.subheader("2. Upload Own")
        uploaded_file = st.file_uploader("Drop PNG/JPG Logo", type=["png", "jpg", "jpeg"])
        if uploaded_file:
            encoded = base64.b64encode(uploaded_file.read()).decode()
            st.session_state.active_graphic = f"data:image/png;base64,{encoded}"

        st.divider()
        st.subheader("3. Graphic Controls")
        g_scale = st.slider("Scale", 0.1, 1.5, 0.5)
        g_x = st.slider("X Position", 0, BASE_SIZE, BASE_SIZE//2)
        g_y = st.slider("Y Position", 0, BASE_SIZE, BASE_SIZE//2)

        st.divider()
        st.subheader("4. Text Layer")
        user_text = st.text_input("Shirt Text", "")
        t_size = st.slider("Font Size", 20, 500, 100)
        t_x = st.slider("Text X", 0, BASE_SIZE, BASE_SIZE//2)
        t_y = st.slider("Text Y", 0, BASE_SIZE, 600)
        t_color = st.color_picker("Text Color", "#000000")

    with view_col:
        # Load the base image (Mockup or Empty Canvas)
        canvas = get_img(MOCKUPS[base_choice])
        
        if canvas:
            # Force size to 2000x2000 for standard design math
            canvas = canvas.resize((BASE_SIZE, BASE_SIZE), Image.LANCZOS)
            draw = ImageDraw.Draw(canvas)

            # LAYER 1: GRAPHIC OVERLAY
            if "active_graphic" in st.session_state:
                overlay = get_img(st.session_state.active_graphic)
                if overlay:
                    # Scaling logic (Maintains aspect ratio)
                    new_w = int(BASE_SIZE * g_scale)
                    new_h = int(overlay.height * (new_w / overlay.width))
                    overlay = overlay.resize((new_w, new_h), Image.LANCZOS)
                    # Paste centered on sliders
                    canvas.paste(overlay, (g_x - new_w//2, g_y - new_h//2), overlay)

            # LAYER 2: TEXT OVERLAY
            if user_text:
                try:
                    # Uses font_size parameter supported in newer Pillow
                    draw.text((t_x, t_y), user_text, fill=t_color, anchor="mm", font_size=t_size)
                except:
                    # Basic fallback if Pillow version is older
                    draw.text((t_x, t_y), user_text, fill=t_color, anchor="mm")

            st.image(canvas, use_container_width=True, caption=f"Studio Render: {base_choice}")
            
            # EXPORT BUTTON
            buf = BytesIO()
            canvas.save(buf, format="PNG")
            st.download_button("💾 Download Design", buf.getvalue(), "gemini_export.png", use_container_width=True)
        else:
            st.error("Error: The base template could not be loaded. Check your worker proxy.")
