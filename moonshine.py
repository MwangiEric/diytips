import streamlit as st
import requests
import base64
from PIL import Image, ImageDraw
from io import BytesIO

# --- CONFIG ---
CORS_PROXY = "https://cors.ericmwangi13.workers.dev/?url="
BASE_SIZE = 2000 

MOCKUPS = {
    "Empty Canvas": "INTERNAL",
    "Premium Black Shirt": "https://ik.imagekit.io/ericmwangi/_Pngtree_premium%20black%20t%20shirt%20mockup_18848206.png",
    "Standard Black Shirt": "https://ik.imagekit.io/ericmwangi/tshtblck.png",
    "Realistic White Shirt": "https://ik.imagekit.io/ericmwangi/_Pngtree_realistic%20white%20t%20shirt%20vector_8963503.png"
}

# --- CORE ENGINE ---
def get_raw_data(url):
    """Fetches binary data directly. Fixes the download/loading issues."""
    if not url or url == "INTERNAL": return None
    u = str(url).strip()
    if u.startswith("//"): u = "https:" + u
    target = f"{CORS_PROXY}{u}" if "http" in u and CORS_PROXY not in u else u
    try:
        r = requests.get(target, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        return r.content if r.status_code == 200 else None
    except: return None

def to_pil(source):
    """RGBA conversion engine for both base layers and overlays."""
    if source == "INTERNAL": 
        return Image.new("RGBA", (BASE_SIZE, BASE_SIZE), (255, 255, 255, 255))
    try:
        if source.startswith("data:image"):
            return Image.open(BytesIO(base64.b64decode(source.split(",")[1]))).convert("RGBA")
        data = get_raw_data(source)
        return Image.open(BytesIO(data)).convert("RGBA") if data else None
    except: return None

# --- UI STATE ---
st.set_page_config(layout="wide")
if "active_asset" not in st.session_state: st.session_state.active_asset = None
if "pos_x" not in st.session_state: st.session_state.pos_x = 1000
if "pos_y" not in st.session_state: st.session_state.pos_y = 1000
if "results" not in st.session_state: st.session_state.results = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("Studio Controls")
    q = st.text_input("Search Assets", "Lion")
    if st.button("Search", use_container_width=True):
        r = requests.get(f"https://moon-shine.vercel.app/api/search", params={"q": q, "limit": 24})
        if r.status_code == 200:
            st.session_state.results = r.json().get("results", {}).get("assets", [])

# --- TABS ---
t_grid, t_canvas = st.tabs(["Discovery", "Design Canvas"])

with t_grid:
    if st.session_state.results:
        cols = st.columns(6)
        for i, item in enumerate(st.session_state.results):
            with cols[i % 6]:
                # Thumbnail preview fix
                thumb = item["thumbnail_src"]
                if thumb.startswith("//"): thumb = "https:" + thumb
                st.image(thumb, use_container_width=True)
                
                c1, c2 = st.columns(2)
                if c1.button("➕", key=f"a_{i}"): 
                    st.session_state.active_asset = item["img_url"]
                
                # ACTUAL DOWNLOAD (Binary data)
                asset_data = get_raw_data(item["img_url"])
                if asset_data:
                    c2.download_button("💾", asset_data, f"asset_{i}.png", key=f"d_{i}")

with t_canvas:
    ctrl, view = st.columns([1, 2.5])
    with ctrl:
        mockup_choice = st.selectbox("Mockup Base", list(MOCKUPS.keys()))
        scale = st.slider("Asset Scale", 0.1, 2.0, 0.5)
        st.session_state.pos_x = st.slider("X Position", 0, 2000, st.session_state.pos_x)
        st.session_state.pos_y = st.slider("Y Position", 0, 2000, st.session_state.pos_y)
        
        txt_input = st.text_input("Design Text")
        txt_col = st.color_picker("Text Color", "#000000")
        
        if st.button("🔄 Center All", use_container_width=True):
            st.session_state.pos_x, st.session_state.pos_y = 1000, 1000
            st.rerun()

    with view:
        # 1. Base Mockup Layer
        canvas = to_pil(MOCKUPS[mockup_choice])
        if canvas:
            canvas = canvas.resize((BASE_SIZE, BASE_SIZE), Image.LANCZOS)
            
            # 2. Asset Layer (The Alpha Mask Fix)
            if st.session_state.active_asset:
                overlay = to_pil(st.session_state.active_asset)
                if overlay:
                    w = int(BASE_SIZE * scale)
                    h = int(overlay.height * (w / overlay.width))
                    overlay = overlay.resize((w, h), Image.LANCZOS)
                    # PASTE: Image, Box, Mask (Mask = Transparency)
                    canvas.paste(overlay, (st.session_state.pos_x - w//2, st.session_state.pos_y - h//2), overlay)
            
            # 3. Text Layer
            if txt_input:
                draw = ImageDraw.Draw(canvas)
                draw.text((st.session_state.pos_x, st.session_state.pos_y - 250), txt_input, fill=txt_col, anchor="mm", font_size=120)
            
            # PREVIEW & FINAL EXPORT
            st.image(canvas, use_container_width=True)
            
            final_buf = BytesIO()
            canvas.save(final_buf, format="PNG")
            st.download_button("Download High-Res Design", final_buf.getvalue(), "final_design.png", use_container_width=True)
