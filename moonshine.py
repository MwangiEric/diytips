import streamlit as st
import requests
import base64
from PIL import Image, ImageDraw
from io import BytesIO

# ============================================================================
# CONFIGURATION
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
# ROBUST IMAGE HANDLING
# ============================================================================
def get_raw_bytes(url):
    """Fetches actual image data for downloads and PIL processing."""
    if not url: return None
    try:
        # Clean protocol-relative URLs
        target = str(url)
        if target.startswith("//"): target = "https:" + target
        
        # Apply Proxy
        if "http" in target and CORS_PROXY not in target:
            target = f"{CORS_PROXY}{target}"
            
        resp = requests.get(target, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if resp.status_code == 200:
            return resp.content
        return None
    except:
        return None

def load_to_pil(data_source):
    """Converts URLs or Base64 into a usable RGBA PIL Image."""
    if not data_source: return None
    try:
        if data_source.startswith("data:image"):
            _, encoded = data_source.split(",", 1)
            return Image.open(BytesIO(base64.b64decode(encoded))).convert("RGBA")
        
        img_bytes = get_raw_bytes(data_source)
        if img_bytes:
            return Image.open(BytesIO(img_bytes)).convert("RGBA")
    except:
        return None
    return None

# ============================================================================
# APP UI & SIDEBAR
# ============================================================================
st.set_page_config(page_title="Gemini Design Studio", layout="wide")

with st.sidebar:
    st.title("⚙️ Studio Controls")
    q_input = st.text_input("Search Assets", "Lion")
    t_input = st.selectbox("Style", ["None", "animals", "graffiti", "typography", "reggae", "streetwear"])
    
    if st.button("🔍 Search API", use_container_width=True, type="primary"):
        params = {"q": q_input, "limit": 30}
        if t_input != "None": params["t"] = t_input
        r = requests.get(f"{API_URL}/api/search", params=params)
        if r.status_code == 200:
            data = r.json()
            st.session_state.results = data.get("results", {}).get("assets", [])
            st.session_state.chips = data.get("suggestions", {}).get("keywords", [])

    if "chips" in st.session_state:
        st.divider()
        st.subheader("✨ Suggestions")
        for sug in st.session_state.chips[:10]:
            if st.button(f"#{sug['keyword']}", key=f"s_{sug['keyword']}", use_container_width=True):
                st.toast(f"Try searching '{sug['keyword']}'")

# ============================================================================
# MAIN TABS
# ============================================================================
tab_grid, tab_design = st.tabs(["🖼️ Asset Discovery", "👕 Design Canvas"])

# --- DISCOVERY TAB ---
with tab_grid:
    if "results" in st.session_state:
        cols = st.columns(6)
        for idx, item in enumerate(st.session_state.results):
            with cols[idx % 6]:
                # Fix display URL
                t_url = item.get("thumbnail_src", "")
                if t_url.startswith("//"): t_url = "https:" + t_url
                st.image(t_url, use_container_width=True)
                
                c1, c2 = st.columns(2)
                if c1.button("➕", key=f"sel_{idx}", help="Send to Canvas"):
                    st.session_state.active_graphic = item.get("img_url")
                    st.toast("Graphic Added to Design Tab!")
                
                # FIXED DOWNLOAD: Fetching bytes first
                raw_url = item.get("img_url", "")
                if raw_url:
                    asset_bytes = get_raw_bytes(raw_url)
                    if asset_bytes:
                        c2.download_button("💾", data=asset_bytes, file_name=f"asset_{idx}.png")

# --- DESIGN TAB ---
with tab_design:
    tool_col, view_col = st.columns([1, 2.5])
    
    with tool_col:
        st.subheader("1. Template")
        base_choice = st.selectbox("Mockup Base", list(MOCKUPS.keys()), index=0)
        
        st.divider()
        st.subheader("2. Upload Own")
        up_file = st.file_uploader("PNG/JPG", type=["png", "jpg", "jpeg"])
        if up_file:
            st.session_state.active_graphic = f"data:image/png;base64,{base64.b64encode(up_file.read()).decode()}"

        st.divider()
        st.subheader("3. Placement")
        g_scale = st.slider("Size", 0.1, 1.5, 0.5)
        g_x = st.slider("Horizontal (X)", 0, BASE_SIZE, BASE_SIZE//2)
        g_y = st.slider("Vertical (Y)", 0, BASE_SIZE, 800)

        st.divider()
        st.subheader("4. Text")
        txt = st.text_input("Jersey Text", "")
        txt_size = st.slider("Font Size", 20, 400, 100)
        txt_x = st.slider("Text X", 0, BASE_SIZE, BASE_SIZE//2)
        txt_y = st.slider("Text Y", 0, BASE_SIZE, 500)
        txt_color = st.color_picker("Text Color", "#000000")

    with view_col:
        # Load Base (2000x2000)
        canvas = load_to_pil(MOCKUPS[base_choice])
        
        if canvas:
            canvas = canvas.resize((BASE_SIZE, BASE_SIZE), Image.LANCZOS)
            draw = ImageDraw.Draw(canvas)

            # LAYER 1: GRAPHIC (With Alpha Mask Fix)
            if "active_graphic" in st.session_state:
                overlay = load_to_pil(st.session_state.active_graphic)
                if overlay:
                    w = int(BASE_SIZE * g_scale)
                    h = int(overlay.height * (w / overlay.width))
                    overlay = overlay.resize((w, h), Image.LANCZOS)
                    # The mask (3rd param) is what makes it visible/transparent correctly
                    canvas.paste(overlay, (g_x - w//2, g_y - h//2), overlay)

            # LAYER 2: TEXT
            if txt:
                try:
                    draw.text((txt_x, txt_y), txt, fill=txt_color, anchor="mm", font_size=txt_size)
                except:
                    draw.text((txt_x, txt_y), txt, fill=txt_color, anchor="mm")

            st.image(canvas, use_container_width=True, caption="2000x2000 Production Preview")
            
            # DOWNLOAD FINAL DESIGN
            buf = BytesIO()
            canvas.save(buf, format="PNG")
            st.download_button("💾 Download Finished Design", buf.getvalue(), "mockup_final.png", use_container_width=True)
        else:
            st.warning("Please select an asset or refresh the page to load the canvas.")
