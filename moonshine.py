import streamlit as st
import requests
from PIL import Image
from io import BytesIO
from streamlit_image_select import image_select

# --- CONFIG ---
SEARX_URL = "https://far-paule-emw-a67bd497.koyeb.app/search"

def analyze_assets(img_url):
    """Samples colors and checks for transparency/background type."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(img_url, headers=headers, timeout=5)
        img = Image.open(BytesIO(response.content))
        
        # 1. Color Sampling
        rgb_img = img.convert("RGB")
        r_e, g_e, b_e = rgb_img.getpixel((5, 5))
        edge_hex = f"#{r_e:02x}{g_e:02x}{b_e:02x}"
        
        avg_img = rgb_img.resize((1, 1), resample=Image.Resampling.BOX)
        r_a, g_a, b_a = avg_img.getpixel((0, 0))
        dom_hex = f"#{r_a:02x}{g_a:02x}{b_a:02x}"
        
        # 2. Transparency Check
        has_alpha = img.mode == 'RGBA'
        is_white_bg = (r_e > 240 and g_e > 240 and b_e > 240)
        
        return edge_hex, dom_hex, has_alpha, is_white_bg, None
    except Exception as e:
        return "#FFFFFF", "#F0F0F0", False, False, str(e)

# --- UI SETUP ---
st.set_page_config(page_title="Pro Print Architect", layout="wide")

if "results" not in st.session_state: st.session_state.results = []

st.title("👕 Pro Print Architect")

query = st.text_input("Design Theme", placeholder="Search for graphics...")

if query and query != st.session_state.get("last_q"):
    st.session_state.last_q = query
    r = requests.get(SEARX_URL, params={"q": f"{query} graphic", "format": "json"}).json()
    st.session_state.results = [i for i in r.get("results", []) if i.get("img_src")]

if st.session_state.results:
    valid_data = st.session_state.results
    thumbs = [i.get('thumbnail_src') for i in valid_data if i.get('thumbnail_src')]
    
    selected_idx = image_select("Choose Graphic", thumbs, key=f"gal_{len(valid_data)}")

    if selected_idx is not None:
        chosen = valid_data[selected_idx]
        edge, dominant, alpha, white_bg, error = analyze_assets(chosen['img_src'])
        
        st.divider()
        col1, col2 = st.columns([1, 1])
        
        with col2:
            st.subheader("🎨 Production Controls")
            
            # Smart Background Suggestion
            use_multiply = False
            if not alpha and white_bg:
                st.warning("💡 Detects white background. 'Multiply' blend mode recommended.")
                use_multiply = st.checkbox("Apply Multiply (Remove White)", value=True)
            
            # Color Selection
            dye_mode = st.radio("Fabric Dye Mode", ["Edge Match", "Average Vibe"], horizontal=True)
            base_color = edge if "Edge" in dye_mode else dominant
            final_color = st.color_picker("Adjust Shirt Color", base_color)
            
            # Contrast Logic (Designer check)
            lum = (0.299 * int(final_color[1:3], 16) + 0.587 * int(final_color[3:5], 16) + 0.114 * int(final_color[5:7], 16))
            text_color = "white" if lum < 128 else "black"

        with col1:
            # PROFESSIONAL MOCKUP
            blend = "multiply" if use_multiply else "normal"
            
            st.html(f"""
            <div style="background-color: {final_color}; width: 100%; max-width: 400px; height: 500px; margin: auto; display: flex; align-items: center; justify-content: center; border-radius: 15px; border: 1px solid #ddd; position: relative;">
                <img src="{chosen['img_src']}" style="width: 70%; mix-blend-mode: {blend}; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));">
                <div style="position: absolute; bottom: 10px; color: {text_color}; opacity: 0.5; font-size: 10px;">
                    DYE: {final_color.upper()} | BLEND: {blend.upper()}
                </div>
            </div>
            """)
