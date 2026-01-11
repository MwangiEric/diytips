import streamlit as st
import requests
import base64
from PIL import Image, ImageEnhance, ImageOps
from io import BytesIO
from rembg import remove
from streamlit_image_select import image_select

# --- 1. CONSTANTS & SECRETS ---
CANVAS_W, CANVAS_H = 1000, 1200
API_ENDPOINT = st.secrets.get("SEARCH_API_URL", "https://far-paule-emw-a67bd497.koyeb.app/search")

def load_local_map(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: return None

def get_dominant_color(pil_img):
    img = pil_img.copy().convert("RGB").resize((1, 1), resample=Image.Resampling.LANCZOS)
    return '#{:02x}{:02x}{:02x}'.format(*img.getpixel((0, 0)))

# --- 2. INITIALIZATION ---
st.set_page_config(layout="wide", page_title="Master Hoodie Studio")

if "results" not in st.session_state: st.session_state.results = []
if "page_offset" not in st.session_state: st.session_state.page_offset = 1
if "processed_design" not in st.session_state: st.session_state.processed_design = None
if "auto_color" not in st.session_state: st.session_state.auto_color = "#121212"

VIBE_MAP = {
    "All": "graphic vector",
    "Symbols": "minimalist symbol vector icon",
    "Graffiti": "graffiti tag street art",
    "Animals": "animal illustration mascot",
    "Nature": "nature vector botanical"
}

# --- 3. TOP BAR UI ---
selected_cat = st.selectbox("🎯 Category Filter", list(VIBE_MAP.keys()), index=0)

col_search, col_btn = st.columns([4, 1])
with col_search:
    query = st.text_input("🔍 Search Topic", placeholder="Type your design idea...")
with col_btn:
    # MANUAL SEARCH BUTTON
    run_search = st.button("Search Designs", use_container_width=True, type="primary")

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("📐 Placement")
    view = st.radio("View", ["Front", "Back"])
    mask_b64 = load_local_map(f"mockups/hoodie_{view.lower()}.png")
    
    v_pos = st.slider("Vertical Pos (px)", 0, 1200, 450)
    design_w = st.slider("Width (px)", 100, 850, 420)

    st.header("🎨 Adjustments")
    bright = st.slider("Brightness", 0.5, 2.0, 1.0)
    cont = st.slider("Contrast", 0.5, 2.0, 1.0)
    sat = st.slider("Saturation", 0.0, 2.0, 1.0)
    col_f1, col_f2 = st.columns(2)
    with col_f1: is_gray = st.toggle("Grayscale")
    with col_f2: is_inv = st.toggle("Invert")

# --- 5. SEARCH ENGINE LOGIC ---
def execute_search(q, cat, page):
    prefix = "" if cat == "All" else f"{VIBE_MAP[cat]} "
    full_q = f"{prefix}{q}".strip()
    params = {
        "q": full_q, 
        "engines": "bing images,unsplash,flickr", 
        "format": "json",
        "pageno": page
    }
    try:
        r = requests.get(API_ENDPOINT, params=params, timeout=15).json()
        return [res for res in r.get("results", []) if (res.get("img_src") or res.get("image"))]
    except:
        st.error("Search failed. Check API connection.")
        return []

if run_search and query:
    st.session_state.page_offset = 1
    st.session_state.results = execute_search(query, selected_cat, 1)
    st.session_state.processed_design = None

# --- 6. GALLERY & RENDERING ---
if st.session_state.results:
    thumbs = [item.get('thumbnail_src') or item.get('thumbnail') or item.get('img_src') for item in st.session_state.results]
    
    # Show thumbnails in a grid or selector
    selection = image_select("Select Artwork", thumbs, return_value="index")

    # SEE MORE BUTTON
    if st.button("➕ See More Designs", use_container_width=True):
        st.session_state.page_offset += 1
        more_results = execute_search(query, selected_cat, st.session_state.page_offset)
        st.session_state.results.extend(more_results)
        st.rerun()

    if isinstance(selection, int):
        chosen = st.session_state.results[selection]
        img_url = chosen.get('img_src') or chosen.get('image')
        
        col_mock, col_ctrl = st.columns([1.6, 1])
        
        with col_ctrl:
            st.subheader("🛠️ Action Center")
            if st.button("🚀 Process & Render", use_container_width=True, type="primary"):
                with st.spinner("Stitching production file..."):
                    resp = requests.get(img_url, timeout=15)
                    raw = Image.open(BytesIO(resp.content))
                    st.session_state.auto_color = get_dominant_color(raw)
                    
                    # Apply Tuning + Rembg
                    img = raw.convert("RGB")
                    img = ImageEnhance.Brightness(img).enhance(bright)
                    img = ImageEnhance.Contrast(img).enhance(cont)
                    img = ImageEnhance.Color(img).enhance(sat)
                    if is_gray: img = ImageOps.grayscale(img).convert("RGB")
                    if is_inv: img = ImageOps.invert(img)
                    
                    st.session_state.processed_design = remove(img)

        with col_mock:
            f_dye = st.session_state.auto_color
            if st.session_state.processed_design:
                # 1000x1200 Production Assembly
                base = Image.new("RGBA", (CANVAS_W, CANVAS_H), f_dye)
                graphic = st.session_state.processed_design
                aspect = graphic.height / graphic.width
                gh = int(design_w * aspect)
                graphic = graphic.resize((design_w, gh), Image.Resampling.LANCZOS)
                
                base.paste(graphic, ((CANVAS_W - design_w)//2, v_pos), graphic)
                
                buf = BytesIO()
                base.save(buf, format="PNG")
                render_b64 = base64.b64encode(buf.getvalue()).decode()
                
                st.html(f"""
                <div style="position: relative; width: 450px; height: 540px; margin: auto; background-color: {f_dye}; border-radius: 20px; overflow: hidden; box-shadow: 0 40px 80px rgba(0,0,0,0.5);">
                    <img src="data:image/png;base64,{render_b64}" style="width: 100%; height: 100%; z-index: 2;">
                    <img src="data:image/png;base64,{mask_b64}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 5; pointer-events: none; opacity: 0.85;">
                </div>
                """)
                st.download_button("💾 Download Master PNG", buf.getvalue(), "hoodie_master.png")
