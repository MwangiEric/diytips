import streamlit as st
import requests
import base64
from PIL import Image, ImageDraw
from io import BytesIO

# ============================================================================
# CONFIG
# ============================================================================
API_URL = "https://moon-shine.vercel.app"
CORS_PROXY = "https://cors.ericmwangi13.workers.dev/?url="
BASE_SIZE = 2000 

MOCKUPS = {
    "Empty Canvas": "https://placehold.co/2000x2000/FFFFFF/png?text=+",
    "Premium Black Shirt": "https://ik.imagekit.io/ericmwangi/_Pngtree_premium%20black%20t%20shirt%20mockup_18848206.png",
    "Standard Black Shirt": "https://ik.imagekit.io/ericmwangi/tshtblck.png",
    "Realistic White Shirt": "https://ik.imagekit.io/ericmwangi/_Pngtree_realistic%20white%20t%20shirt%20vector_8963503.png"
}

# ============================================================================
# LOGIC FIX: CACHED IMAGE FETCHING
# ============================================================================

@st.cache_data(show_spinner=False)
def fetch_image_raw(url):
    """Fetches bytes. Cached to prevent 'off' logic during slider moves."""
    if not url: return None
    try:
        target = str(url)
        if target.startswith("//"): target = "https:" + target
        if "http" in target and CORS_PROXY not in target:
            target = f"{CORS_PROXY}{target}"
            
        resp = requests.get(target, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        return resp.content if resp.status_code == 200 else None
    except:
        return None

def process_pil(source):
    """Logic fix: Ensures RGBA mode so transparency 'pasting' works."""
    if not source: return None
    try:
        if source.startswith("data:image"):
            _, encoded = source.split(",", 1)
            return Image.open(BytesIO(base64.b64decode(encoded))).convert("RGBA")
        
        img_bytes = fetch_image_raw(source)
        if img_bytes:
            return Image.open(BytesIO(img_bytes)).convert("RGBA")
    except:
        return None
    return None

# ============================================================================
# UI
# ============================================================================
st.set_page_config(layout="wide")

# Persistent State Initialization
if "active_graphic" not in st.session_state:
    st.session_state.active_graphic = None

with st.sidebar:
    st.title("⚙️ Studio")
    q = st.text_input("Search", "Lion")
    if st.button("🔍 Run Search", use_container_width=True):
        res = requests.get(f"{API_URL}/api/search", params={"q": q, "limit": 12})
        if res.status_code == 200:
            st.session_state.results = res.json().get("results", {}).get("assets", [])

# --- TABS ---
t1, t2 = st.tabs(["🖼️ Grid", "👕 Canvas"])

with t1:
    if "results" in st.session_state:
        cols = st.columns(4)
        for i, item in enumerate(st.session_state.results):
            with cols[i % 4]:
                st.image(item["thumbnail_src"], use_container_width=True)
                # LOGIC FIX: Use callback to prevent state loss
                if st.button("Select", key=f"btn_{i}", use_container_width=True):
                    st.session_state.active_graphic = item["img_url"]
                    st.toast("Graphic Active!")

with t2:
    ctrl, view = st.columns([1, 2.5])
    
    with ctrl:
        base_name = st.selectbox("Base", list(MOCKUPS.keys()))
        scale = st.slider("Scale", 0.1, 1.5, 0.5)
        # LOGIC FIX: Position sliders center on 2000
        x_pos = st.slider("X", 0, 2000, 1000)
        y_pos = st.slider("Y", 0, 2000, 1000)
        
        if st.button("Clear Design"):
            st.session_state.active_graphic = None
            st.rerun()

    with view:
        # 1. Start with Base
        base_img = process_pil(MOCKUPS[base_name])
        
        if base_img:
            # Force 2000x2000
            canvas = base_img.resize((BASE_SIZE, BASE_SIZE), Image.LANCZOS)
            
            # 2. Layer the Graphic
            if st.session_state.active_graphic:
                overlay = process_pil(st.session_state.active_graphic)
                if overlay:
                    # Logic: Resize overlay based on scale
                    new_w = int(BASE_SIZE * scale)
                    ratio = overlay.height / overlay.width
                    new_h = int(new_w * ratio)
                    overlay = overlay.resize((new_w, new_h), Image.LANCZOS)
                    
                    # Logic: Calculate top-left corner from center slider
                    paste_x = x_pos - (new_w // 2)
                    paste_y = y_pos - (new_h // 2)
                    
                    # LOGIC FIX: The 3rd argument 'overlay' is the transparency mask
                    canvas.paste(overlay, (paste_x, paste_y), overlay)

            # Display
            st.image(canvas, use_container_width=True)
            
            # Export
            out = BytesIO()
            canvas.save(out, format="PNG")
            st.download_button("💾 Download PNG", out.getvalue(), "design.png", use_container_width=True)
