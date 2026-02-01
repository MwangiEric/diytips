import streamlit as st
import requests
import base64
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# ============================================================================
# CONFIGURATION
# ============================================================================
API_URL = "https://moon-shine.vercel.app"
CORS_PROXY = "https://cors.ericmwangi13.workers.dev/?url="
BASE_SIZE = 2000 

# Updated Mockup URLs as provided
MOCKUPS = {
    "Empty Canvas": "https://placehold.co/2000x2000/FFFFFF/png?text=+",
    "Premium Black Shirt": "https://ik.imagekit.io/ericmwangi/_Pngtree_premium%20black%20t%20shirt%20mockup_18848206.png",
    "Standard Black Shirt": "https://ik.imagekit.io/ericmwangi/tshtblck.png",
    "Realistic White Shirt": "https://ik.imagekit.io/ericmwangi/_Pngtree_realistic%20white%20t%20shirt%20vector_8963503.png"
}

# Fallback font [2026-01-15]
ST_FONT_STYLE = "sans-serif"

def get_img(input_data):
    """Universal loader for URLs and Base64 strings."""
    if not input_data: return None
    try:
        if isinstance(input_data, str) and input_data.startswith("data:image"):
            _, encoded = input_data.split(",", 1)
            return Image.open(BytesIO(base64.b64decode(encoded))).convert("RGBA")
        
        target = f"{CORS_PROXY}{input_data}" if "http" in input_data and CORS_PROXY not in input_data else input_data
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(target, headers=headers, timeout=15)
        if resp.status_code == 200:
            return Image.open(BytesIO(resp.content)).convert("RGBA")
    except:
        return None

# ============================================================================
# INTERFACE SETUP
# ============================================================================
st.set_page_config(page_title="Gemini Design Studio", layout="wide")

# SIDEBAR: Inputs & Suggestions
with st.sidebar:
    st.title("⚙️ Studio Controls")
    q_input = st.text_input("Keywords", "Lion")
    t_input = st.selectbox("Style Category", ["None", "animals", "graffiti", "typography", "reggae", "streetwear"])
    
    if st.button("🔍 Find Assets", use_container_width=True, type="primary"):
        params = {"q": q_input, "limit": 30}
        if t_input != "None": params["t"] = t_input
        r = requests.get(f"{API_URL}/api/search", params=params)
        if r.status_code == 200:
            data = r.json()
            st.session_state.results = data.get("results", {}).get("assets", [])
            st.session_state.chips = data.get("suggestions", {}).get("keywords", [])

    # MOVED: Suggestions in Sidebar
    if "chips" in st.session_state and st.session_state.chips:
        st.divider()
        st.subheader("✨ Keyword Suggestions")
        for sug in st.session_state.chips[:12]:
            if st.button(f"#{sug['keyword']}", key=f"s_{sug['keyword']}", use_container_width=True):
                st.toast(f"Tip: Search for {sug['keyword']}")

# ============================================================================
# MAIN CONTENT
# ============================================================================
tab_discovery, tab_canvas = st.tabs(["🖼️ Asset Discovery", "👕 Design Canvas"])

# DISCOVERY TAB: Grid with Download & Select
with tab_discovery:
    if "results" in st.session_state:
        cols = st.columns(6)
        for idx, item in enumerate(st.session_state.results):
            with cols[idx % 6]:
                st.image(item.get("thumbnail_src"), use_container_width=True)
                c1, c2 = st.columns(2)
                if c1.button("➕", key=f"sel_{idx}", help="Select for Canvas"):
                    st.session_state.active_graphic = item.get("img_url")
                    st.toast("Graphic Loaded!")
                
                # SEPARATE DOWNLOAD: Added as requested
                img_url = item.get("img_url")
                if img_url:
                    c2.download_button("💾", data=img_url, file_name=f"asset_{idx}.png", help="Download Asset Separately")

# CANVAS TAB: Mockups & Controls
with tab_canvas:
    tool_col, view_col = st.columns([1, 2.5])
    
    with tool_col:
        st.subheader("1. Template Selection")
        # Default is 2000x2000 Empty Canvas (index 0)
        base_choice = st.selectbox("Mockup Base", list(MOCKUPS.keys()), index=0)
        
        st.divider()
        st.subheader("2. File Upload")
        uploaded_file = st.file_uploader("Upload Logo", type=["png", "jpg", "jpeg"])
        if uploaded_file:
            encoded = base64.b64encode(uploaded_file.read()).decode()
            st.session_state.active_graphic = f"data:image/png;base64,{encoded}"

        st.divider()
        st.subheader("3. Graphic Controls")
        g_scale = st.slider("Graphic Size", 0.1, 1.5, 0.5)
        g_x = st.slider("Graphic X Position", 0, BASE_SIZE, BASE_SIZE//2)
        g_y = st.slider("Graphic Y Position", 0, BASE_SIZE, BASE_SIZE//2)

        st.divider()
        st.subheader("4. Text Controls")
        user_text = st.text_input("Shirt Text", "")
        t_size = st.slider("Text Size", 20, 500, 100)
        t_x = st.slider("Text X Position", 0, BASE_SIZE, BASE_SIZE//2)
        t_y = st.slider("Text Y Position", 0, BASE_SIZE, 600)
        t_color = st.color_picker("Text Color", "#FFFFFF")

    with view_col:
        with st.spinner("Rendering Layered Design..."):
            # A. Base Layer
            canvas = get_img(MOCKUPS[base_choice])
            if canvas:
                canvas = canvas.resize((BASE_SIZE, BASE_SIZE), Image.LANCZOS)
                draw = ImageDraw.Draw(canvas)

                # B. Graphic Layer
                if "active_graphic" in st.session_state:
                    overlay = get_img(st.session_state.active_graphic)
                    if overlay:
                        new_w = int(BASE_SIZE * g_scale)
                        new_h = int(overlay.height * (new_w / overlay.width))
                        overlay = overlay.resize((new_w, new_h), Image.LANCZOS)
                        canvas.paste(overlay, (g_x - new_w//2, g_y - new_h//2), overlay)

                # C. Text Layer
                if user_text:
                    try:
                        # PIL default font doesn't scale perfectly without .ttf, 
                        # but we use 'font_size' for newer Pillow versions
                        draw.text((t_x, t_y), user_text, fill=t_color, anchor="mm", font_size=t_size)
                    except:
                        draw.text((t_x, t_y), user_text, fill=t_color, anchor="mm")

                st.image(canvas, use_container_width=True, caption="2000x2000 Export Preview")
                
                # D. Export Design
                buf = BytesIO()
                canvas.save(buf, format="PNG")
                st.download_button("💾 Download Finished Mockup", buf.getvalue(), "gemini_studio_export.png", use_container_width=True)
