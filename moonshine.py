import streamlit as st
import requests
import base64
from PIL import Image, ImageDraw
from io import BytesIO

# ============================================================================
# 1. CONFIGURATION
# ============================================================================
API_URL = "https://moon-shine.vercel.app"
CORS_PROXY = "https://cors.ericmwangi13.workers.dev/?url="
BASE_SIZE = 2000 

# Mockup Dictionary: "Empty Canvas" triggers a native Pillow generation
MOCKUPS = {
    "Empty Canvas": "INTERNAL_PILLOW",
    "Premium Black Shirt": "https://ik.imagekit.io/ericmwangi/_Pngtree_premium%20black%20t%20shirt%20mockup_18848206.png",
    "Standard Black Shirt": "https://ik.imagekit.io/ericmwangi/tshtblck.png",
    "Realistic White Shirt": "https://ik.imagekit.io/ericmwangi/_Pngtree_realistic%20white%20t%20shirt%20vector_8963503.png"
}

# ============================================================================
# 2. IMAGE ENGINE (HANDLES URLS, BYTES, AND NATIVE GENERATION)
# ============================================================================

def clean_url(url):
    """Fixes // protocols and applies proxy for external links."""
    if not url or url == "INTERNAL_PILLOW": return None
    u = str(url).strip()
    if u.startswith("//"):
        u = "https:" + u
    if u.startswith("http") and CORS_PROXY not in u:
        return f"{CORS_PROXY}{u}"
    return u

@st.cache_data(show_spinner=False)
def fetch_bytes(url):
    """Fetches raw image data. Cached to speed up slider interactions."""
    target = clean_url(url)
    if not target: return None
    try:
        resp = requests.get(target, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        return resp.content if resp.status_code == 200 else None
    except:
        return None

def load_to_pil(source):
    """Universal loader: Handles Local Base64, Remote URLs, and Pillow Native Canvas."""
    if source == "INTERNAL_PILLOW":
        # Generate a pure white 2000x2000 canvas internally
        return Image.new("RGBA", (BASE_SIZE, BASE_SIZE), (255, 255, 255, 255))
    
    if not source: return None
    try:
        if source.startswith("data:image"):
            _, encoded = source.split(",", 1)
            return Image.open(BytesIO(base64.b64decode(encoded))).convert("RGBA")
        
        raw_data = fetch_bytes(source)
        if raw_data:
            # Pillow auto-detects format (PNG/JPG) from binary headers
            return Image.open(BytesIO(raw_data)).convert("RGBA")
    except:
        return None
    return None

# ============================================================================
# 3. INTERFACE & STATE
# ============================================================================
st.set_page_config(layout="wide", page_title="Gemini Studio Pro")

# Persistent state for the active graphic layer
if "active_graphic" not in st.session_state:
    st.session_state.active_graphic = None

with st.sidebar:
    st.title("⚙️ Studio Controls")
    q_search = st.text_input("Asset Search", "Lion")
    
    if st.button("🔍 Search API", use_container_width=True, type="primary"):
        try:
            r = requests.get(f"{API_URL}/api/search", params={"q": q_search, "limit": 30})
            if r.status_code == 200:
                data = r.json()
                st.session_state.results = data.get("results", {}).get("assets", [])
                st.session_state.chips = data.get("suggestions", {}).get("keywords", [])
        except:
            st.error("Could not connect to API.")

    if "chips" in st.session_state:
        st.divider()
        st.subheader("✨ Suggestions")
        for sug in st.session_state.chips[:8]:
            if st.button(f"#{sug['keyword']}", key=f"s_{sug['keyword']}", use_container_width=True):
                st.toast(f"Try searching '{sug['keyword']}'")

# --- MAIN TABS ---
tab_discovery, tab_design = st.tabs(["🖼️ Discovery", "👕 Design Canvas"])

# TAB 1: ASSET DISCOVERY
with tab_discovery:
    if "results" in st.session_state:
        cols = st.columns(6)
        for idx, item in enumerate(st.session_state.results):
            with cols[idx % 6]:
                # Visual preview fix for browser
                t_prev = clean_url(item["thumbnail_src"])
                st.image(t_prev, use_container_width=True)
                
                c1, c2 = st.columns(2)
                if c1.button("➕", key=f"sel_{idx}", help="Select for Design"):
                    st.session_state.active_graphic = item["img_url"]
                    st.toast("Logo added to Design Tab!")
                
                # Direct byte-download fix
                asset_bytes = fetch_bytes(item["img_url"])
                if asset_bytes:
                    c2.download_button("💾", data=asset_bytes, file_name=f"asset_{idx}.png", key=f"dl_{idx}")

# TAB 2: DESIGN CANVAS
with tab_design:
    tool_col, view_col = st.columns([1, 2.5])
    
    with tool_col:
        st.subheader("1. Template")
        base_choice = st.selectbox("Mockup Base", list(MOCKUPS.keys()), index=0)
        
        st.divider()
        st.subheader("2. Controls")
        g_scale = st.slider("Scale Logo", 0.1, 1.5, 0.5)
        g_x = st.slider("X Position", 0, BASE_SIZE, BASE_SIZE // 2)
        g_y = st.slider("Y Position", 0, BASE_SIZE, 850)
        
        st.divider()
        st.subheader("3. Text Layer")
        user_txt = st.text_input("Jersey Text", "")
        txt_color = st.color_picker("Text Color", "#000000")
        
        if st.button("🔄 Center All", use_container_width=True):
            st.toast("Snap to center applied!")

    with view_col:
        # STEP A: Create/Load Base Canvas
        canvas_pil = load_to_pil(MOCKUPS[base_choice])
        
        if canvas_pil:
            # Resize base to 2000x2000 standard
            canvas = canvas_pil.resize((BASE_SIZE, BASE_SIZE), Image.LANCZOS)
            
            # STEP B: Layer Graphic with Alpha Mask (Fixes "Invisible" issue)
            if st.session_state.active_graphic:
                overlay = load_to_pil(st.session_state.active_graphic)
                if overlay:
                    # Calculate new size while maintaining aspect ratio
                    new_w = int(BASE_SIZE * g_scale)
                    new_h = int(overlay.height * (new_w / overlay.width))
                    overlay = overlay.resize((new_w, new_h), Image.LANCZOS)
                    # PASTE: (Image, Position, Mask) - Mask is what enables transparency
                    canvas.paste(overlay, (g_x - new_w // 2, g_y - new_h // 2), overlay)

            # STEP C: Layer Text
            if user_txt:
                draw = ImageDraw.Draw(canvas)
                # Position text relative to graphic for better layout
                draw.text((g_x, g_y - 250), user_txt, fill=txt_color, anchor="mm", font_size=120)

            # RENDER PREVIEW
            st.image(canvas, use_container_width=True, caption=f"2000x2000 {base_choice}")
            
            # EXPORT FINAL PNG
            export_io = BytesIO()
            canvas.save(export_io, format="PNG")
            st.download_button("💾 Download High-Res Design", export_io.getvalue(), "final_design.png", use_container_width=True)
        else:
            st.error("Canvas failed to load. Please refresh or try another base.")
