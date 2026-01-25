import streamlit as st
import requests
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO

# ============================================================================
# CONFIGURATION & ASSETS
# ============================================================================
API_URL = "https://moon-shine.vercel.app"
# Use a high-quality jersey base if search is empty
DEFAULT_JERSEY = "https://i.imgur.com/your_jersey_template.png" 

def get_pil_image(url):
    try:
        resp = requests.get(url, timeout=10)
        return Image.open(BytesIO(resp.content)).convert("RGBA")
    except:
        return None

# ============================================================================
# APP INTERFACE
# ============================================================================
st.title("⚽ Moonshine Jersey & Streetwear Studio")

tab1, tab2 = st.tabs(["🔍 Calligraphy & Graphics", "👕 Jersey Canvas"])

with tab1:
    st.header("Asset Discovery")
    col_q, col_c = st.columns([2, 1])
    
    with col_q:
        # Default to Graffiti/Calligraphy as requested
        q = st.text_input("Search Styles", "Street Graffiti Tag")
    with col_c:
        c = st.selectbox("Style Category", ["graffiti", "typography", "vectors", "all"])

    if st.button("Search Assets", type="primary"):
        # Utilizing your v3.2.0 API params: e=png, w=500, h=500
        resp = requests.get(f"{API_URL}/api/search", params={"q": q, "c": c, "e": "png", "w": 500, "h": 500})
        st.session_state.search_results = resp.json().get("assets", [])

    if "search_results" in st.session_state:
        cols = st.columns(4)
        for idx, asset in enumerate(st.session_state.search_results):
            with cols[idx % 4]:
                st.image(asset["img"], use_container_width=True)
                if st.button("Use this Style", key=f"sel_{idx}"):
                    st.session_state.selected_asset = asset["img"]
                    st.toast("Style Loaded!")

with tab2:
    if "selected_asset" not in st.session_state:
        st.warning("Please select a Calligraphy or Graffiti piece first.")
    else:
        col_setup, col_render = st.columns([1, 2])

        with col_setup:
            st.subheader("Jersey Specs")
            jersey_q = st.text_input("Jersey Base", "blank soccer jersey front")
            
            # Jersey specific text (Name/Number)
            st.divider()
            player_name = st.text_input("Player Name", "GEMINI")
            player_num = st.text_input("Number", "10")
            text_color = st.color_picker("Print Color", "#FFFFFF")

            # Positioning Sliders
            scale = st.slider("Graphic Scale", 0.1, 1.0, 0.4)
            y_offset = st.slider("Chest Position", 0, 1000, 350)
            
            generate = st.button("🎯 Render Jersey", type="primary", use_container_width=True)

        with col_render:
            if generate:
                with st.spinner("Applying print to jersey..."):
                    # 1. Fetch Jersey Template
                    j_resp = requests.get(f"{API_URL}/api/search", params={"q": jersey_q, "c": "all", "limit": 1})
                    j_data = j_resp.json().get("assets")
                    j_url = j_data[0]["img"] if j_data else DEFAULT_JERSEY
                    
                    # 2. Process Layers
                    jersey = get_pil_image(j_url).resize((1200, 1200))
                    graphic = get_pil_image(st.session_state.selected_asset)
                    
                    # Scale Graphic
                    gw = int(jersey.width * scale)
                    gh = int(gw * (graphic.height / graphic.width))
                    graphic = graphic.resize((gw, gh), Image.Resampling.LANCZOS)
                    
                    # 3. Draw on Canvas
                    draw = ImageDraw.Draw(jersey)
                    
                    # Paste Graffiti/Calligraphy on Chest
                    jersey.alpha_composite(graphic, ((jersey.width - gw)//2, y_offset))
                    
                    # Add Jersey Text (Using standard PIL fonts)
                    # Note: In a real prod env, you'd load a specific 'jersey' font file
                    try:
                        font = ImageFont.load_default() 
                        draw.text((600, y_offset - 100), player_name, fill=text_color, font=font, anchor="mm")
                        draw.text((600, y_offset + gh + 50), player_num, fill=text_color, font=font, anchor="mm")
                    except:
                        pass

                    st.image(jersey, caption="Final Jersey Print Preview", use_container_width=True)
                    
                    # Download
                    buf = BytesIO()
                    jersey.save(buf, format="PNG")
                    st.download_button("📥 Download Print File", buf.getvalue(), "jersey_design.png", "image/png")
