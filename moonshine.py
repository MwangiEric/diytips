import streamlit as st
import requests
from PIL import Image
from io import BytesIO
from streamlit_image_select import image_select

# --- DESIGNER ASSETS ---
SHIRT_MASK = "https://i.imgur.com/8fS73O4.png"
SEARX_URL = "https://far-paule-emw-a67bd497.koyeb.app/search"

def get_edge_color(img_url):
    """Samples the top-left pixel of the image and returns a CSS Hex code."""
    try:
        response = requests.get(img_url, timeout=5)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        # Sample the pixel at the very edge (0,0)
        r, g, b = img.getpixel((5, 5)) # Offset slightly to avoid literal single-pixel artifacts
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception as e:
        return "#FFFFFF" # Fallback to white

# --- SMART QUERY LOGIC ---
def get_smart_query(user_q):
    return f"official graphic vector {user_q} -shirt -mockup -people"

# --- UI SETUP ---
st.set_page_config(page_title="Color-Match Studio", layout="wide")

if "db" not in st.session_state: st.session_state.db = []

st.title("👕 Color-Match Studio")
query = st.text_input("Design Theme", placeholder="e.g. 'Minimalist Japanese Art'")

if query and query != st.session_state.get("last_q"):
    st.session_state.last_q = query
    # Fetch results
    r = requests.get(SEARX_URL, params={"q": get_smart_query(query), "format": "json"}).json()
    st.session_state.db = [i for i in r.get("results", []) if i.get("img_src") and i.get("thumbnail_src")]

if st.session_state.db:
    valid_data = st.session_state.db
    thumbs = [i['thumbnail_src'] for i in valid_data]
    
    selected_idx = image_select("Select Graphic", thumbs, key=f"gallery_{len(valid_data)}")

    if selected_idx is not None:
        chosen = valid_data[selected_idx]
        
        # --- THE SMART COLOR MATCHING ---
        # We sample the edge color of the high-res image
        with st.spinner("Matching fabric dye to design..."):
            auto_color = get_edge_color(chosen['img_src'])
        
        col1, col2 = st.columns([1.2, 1])
        
        with col1:
            # DYNAMIC MOCKUP
            st.html(f"""
            <div style="background-color: {auto_color}; width: 360px; height: 440px; margin: auto; position: relative; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.15); transition: background-color 0.5s ease;">
                
                <div style="position: absolute; top: 25%; left: 50%; transform: translateX(-50%); width: 50%; z-index: 1; mix-blend-mode: multiply;">
                    <img src="{chosen['img_src']}" style="width: 100%;">
                </div>

                <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; pointer-events: none; opacity: 0.6;">
                    <img src="{SHIRT_MASK}" style="width: 100%; height: 100%; object-fit: contain;">
                </div>
            </div>
            """)
        
        with col2:
            st.subheader("🎨 Designer Palette")
            st.write(f"**Matched Dye:** `{auto_color.upper()}`")
            st.color_picker("Override Fabric Color", auto_color)
            
            st.divider()
            st.info(f"**Resolution:** {chosen.get('width')}x{chosen.get('height')}\n\n**Source:** {chosen.get('source')}")
            
            if st.button("🚀 Send to Print Shop", use_container_width=True):
                st.success("Dye color and high-res asset sent!")
