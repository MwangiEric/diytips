import streamlit as st
import requests
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import base64
import json
from streamlit_image_select import image_select

# ============================================================================
# CONFIGURATION
# ============================================================================
API_URL = "https://moon-shine.vercel.app"  # Your API endpoint
SHIRT_MASK = "https://i.imgur.com/8fS73O4.png"  # Fallback for CSS preview

# Session state initialization
if "design_layer" not in st.session_state:
    st.session_state.design_layer = {
        "background": None,
        "graphics": [],
        "texts": [],
        "canvas_size": "1000x1000"
    }

if "search_results" not in st.session_state:
    st.session_state.search_results = []

if "selected_graphic" not in st.session_state:
    st.session_state.selected_graphic = None

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_api_font():
    """Get API's system font info."""
    try:
        resp = requests.get(f"{API_URL}/api/fonts/available", timeout=5)
        if resp.status_code == 200:
            return resp.json().get("system_font")
    except:
        pass
    return "arial.ttf"

def generate_css_preview(fabric_hex, graphic_url, text, text_color="#000000"):
    """Instant CSS-based preview for speed."""
    return f"""
    <div style="background-color: {fabric_hex}; width: 380px; height: 460px; margin: auto; position: relative; border-radius: 20px; overflow: hidden; box-shadow: 0 25px 60px rgba(0,0,0,0.2);">
        <div style="position: absolute; top: 22%; left: 50%; transform: translateX(-50%); width: 45%; z-index: 1; mix-blend-mode: multiply;">
            <img src="{graphic_url}" style="width: 100%;">
            <p style="text-align: center; color: black; font-family: 'Arial', sans-serif; font-weight: 800; margin-top: 15px; font-size: 18px; letter-spacing: 1px;">{text}</p>
        </div>
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; pointer-events: none; opacity: 0.6;">
            <img src="{SHIRT_MASK}" style="width: 100%; height: 100%; object-fit: contain;">
        </div>
    </div>
    """

def reset_design():
    """Reset all design layers."""
    st.session_state.design_layer = {
        "background": None,
        "graphics": [],
        "texts": [],
        "canvas_size": "1000x1000"
    }
    st.session_state.selected_graphic = None

# ============================================================================
# UI COMPONENTS
# ============================================================================

def search_tab():
    """Step 1: Asset discovery."""
    st.header("🔍 Step 1: Asset Discovery")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        query = st.text_input("Design Theme", placeholder="e.g. Vintage Kenyan Wildlife")
    with col2:
        category = st.selectbox("Category", [
            "vectors", "backgrounds", "patterns", "stickers", "labels",
            "graffiti", "typography", "anime", "automotive", "reggae", "kenyan"
        ])
    with col3:
        sites = st.selectbox("Site Filter", ["1", "0", "vecteezy.com", "freepik.com", "pinterest.com"])
    
    # Search button
    if st.button("🔎 Search Assets", type="primary") or query:
        if query:
            with st.spinner("Searching creative assets..."):
                try:
                    # Simplified API query
                    resp = requests.get(
                        f"{API_URL}/api/search",
                        params={"q": query, "c": category, "s": sites, "w": 800, "h": 800, "t": "png"},
                        timeout=10
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.search_results = data.get("assets", [])
                        st.success(f"Found {data.get('count', 0)} assets")
                    else:
                        st.error(f"Search failed: {resp.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
    
    # Gallery display
    if st.session_state.search_results:
        thumbs = [asset["thumb"] for asset in st.session_state.search_results]
        titles = [asset["title"][:30] for asset in st.session_state.search_results]
        
        selected_idx = image_select(
            "Select Your Graphic",
            images=thumbs,
            captions=titles,
            use_container_width=True
        )
        
        if selected_idx is not None:
            st.session_state.selected_graphic = st.session_state.search_results[selected_idx]
            st.session_state.design_layer["graphics"] = [st.session_state.selected_graphic["img"]]

def studio_tab():
    """Step 2: Design composition."""
    st.header("🎨 Step 2: Design Studio")
    
    if not st.session_state.selected_graphic:
        st.warning("⚠️ Please select a graphic first in the Search tab")
        return
    
    col1, col2 = st.columns([1.2, 1])
    
    # Live preview (CSS for speed)
    with col1:
        st.subheader("Live Preview")
        auto_color = requests.get(
            f"{API_URL}/api/search", 
            params={"q": "fabric texture", "c": "backgrounds", "s": "1"}
        ).json()["assets"][0]["img"] if not st.session_state.design_layer["background"] else st.session_state.design_layer["background"]
        
        fabric_color = st.color_picker("Fabric Color", "#FFFFFF", key="fabric")
        text_content = st.text_input("Caption", "DESIGNER SERIES", key="caption")
        text_color = st.color_picker("Text Color", "#000000", key="text_color")
        
        st.html(generate_css_preview(fabric_color, st.session_state.selected_graphic["img"], text_content, text_color))
    
    # Studio controls
    with col2:
        st.subheader("🎛️ Studio Controls")
        
        # Background
        with st.expander("Background Layer", expanded=True):
            bg_url = st.text_input("Background URL", placeholder="Leave empty for solid color")
            if bg_url:
                st.session_state.design_layer["background"] = bg_url
        
        # Text layers
        with st.expander("Text Layers", expanded=True):
            text_count = st.number_input("Number of Text Elements", 1, 5, 1)
            texts = []
            for i in range(text_count):
                col_a, col_b = st.columns(2)
                with col_a:
                    txt = st.text_input(f"Text {i+1}", text_content if i == 0 else "")
                    size = st.slider(f"Size {i+1}", 20, 200, 80)
                with col_b:
                    x = st.slider(f"X Position {i+1}", 0, 1000, 500)
                    y = st.slider(f"Y Position {i+1}", 0, 1000, 600)
                    color = st.color_picker(f"Color {i+1}", text_color)
                
                if txt:
                    texts.append({
                        "text": txt,
                        "size": size,
                        "x": x,
                        "y": y,
                        "color": color,
                        "font_url": None  # Use API's system font
                    })
            
            st.session_state.design_layer["texts"] = texts
        
        # Generate real image
        if st.button("🎯 Generate Real Image", type="primary"):
            with st.spinner("Rendering high-quality design..."):
                try:
                    payload = {
                        "background_url": st.session_state.design_layer.get("background"),
                        "overlay_urls": st.session_state.design_layer["graphics"],
                        "text_elements": st.session_state.design_layer["texts"],
                        "final_size": "1200x1200"
                    }
                    
                    resp = requests.post(f"{API_URL}/api/combine-design", json=payload, timeout=30)
                    
                    if resp.status_code == 200:
                        img = Image.open(BytesIO(resp.content))
                        st.image(img, caption="Rendered Design", use_container_width=True)
                        
                        # Store for mockup
                        buf = BytesIO()
                        img.save(buf, format="PNG")
                        st.session_state.design_layer["rendered"] = base64.b64encode(buf.getvalue()).decode()
                    else:
                        st.error(f"Generation failed: {resp.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Reset button
    if st.button("🗑️ Reset Design"):
        reset_design()
        st.rerun()

def mockup_tab():
    """Step 3: Product mockup generation."""
    st.header("👕 Step 3: Product Mockup")
    
    if not st.session_state.selected_graphic:
        st.warning("⚠️ Please complete Step 1 & 2 first")
        return
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Product Selection")
        
        product_type = st.selectbox("Product", [
            "t-shirt", "hoodie", "cap", "mug", "tank-top", "tote-bag"
        ])
        
        product_color = st.color_picker("Product Color", "#FFFFFF")
        
        # Mockup generation
        if st.button("👕 Generate Mockup", type="primary"):
            design_url = st.session_state.selected_graphic["img"]
            
            # If we have a rendered design, use that
            if "rendered" in st.session_state.design_layer:
                design_url = f"data:image/png;base64,{st.session_state.design_layer['rendered']}"
            
            with st.spinner(f"Creating {product_type} mockup..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/api/generate-mockup",
                        json={
                            "design_url": design_url,
                            "product_type": product_type,
                            "color": product_color,
                            "image_size": "1200x1200"
                        },
                        timeout=30
                    )
                    
                    if resp.status_code == 200:
                        img = Image.open(BytesIO(resp.content))
                        st.image(img, caption=f"{product_type.title()} Mockup", use_container_width=True)
                        
                        # Download
                        buf = BytesIO()
                        img.save(buf, format="PNG")
                        st.download_button(
                            label="📥 Download Mockup",
                            data=buf.getvalue(),
                            file_name=f"{product_type}_mockup.png",
                            mime="image/png",
                            use_container_width=True
                        )
                    else:
                        st.error(f"Mockup failed: {resp.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        st.subheader("Quick Preview")
        # Show a simple preview of selected product
        st.image(SHIRT_MASK, width=300, caption="Product Template")

def export_tab():
    """Step 4: High-res print export."""
    st.header("📦 Step 4: Print-Ready Export")
    
    if not st.session_state.selected_graphic:
        st.warning("⚠️ Please complete a design first")
        return
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Export Settings")
        
        # Print shop specifications
        resolution = st.select_slider(
            "Resolution (DPI equivalent)", 
            options=["72dpi (Screen)", "150dpi (Good)", "300dpi (Print)", "600dpi (Ultra)"],
            value="300dpi (Print)"
        )
        
        dimensions = st.selectbox(
            "Canvas Size", 
            ["3000x3000", "4000x4000", "5000x5000", "6000x6000"]
        )
        
        fabric_color = st.color_picker("Fabric Base Color", "#FFFFFF")
        include_bleed = st.checkbox("Add Print Bleed (0.125in)", value=True)
        
        # Generate print file
        if st.button("🚀 GENERATE PRINT FILE", type="primary"):
            with st.spinner("Baking high-resolution print file..."):
                try:
                    # Use API to generate massive canvas
                    payload = {
                        "background_url": None,  # Use solid color
                        "overlay_urls": st.session_state.design_layer["graphics"],
                        "text_elements": st.session_state.design_layer["texts"],
                        "final_size": dimensions
                    }
                    
                    resp = requests.post(f"{API_URL}/api/combine-design", json=payload, timeout=45)
                    
                    if resp.status_code == 200:
                        img = Image.open(BytesIO(resp.content))
                        
                        # Apply fabric color as background
                        if fabric_color != "#FFFFFF":
                            bg = Image.new("RGB", img.size, fabric_color)
                            bg.paste(img, (0, 0), img)
                            img = bg
                        
                        st.image(img, caption="Print-Ready File", use_container_width=True)
                        
                        # Download
                        buf = BytesIO()
                        img.save(buf, format="PNG")
                        st.download_button(
                            label="📦 DOWNLOAD FOR PRINT SHOP",
                            data=buf.getvalue(),
                            file_name=f"print_ready_{st.session_state.selected_graphic['title'][:20]}.png",
                            mime="image/png",
                            use_container_width=True
                        )
                        
                        # Print specs
                        with st.expander("📋 Print Specifications"):
                            st.json({
                                "resolution": resolution,
                                "dimensions": dimensions,
                                "color_profile": "sRGB",
                                "bleed": include_bleed,
                                "format": "PNG"
                            })
                    else:
                        st.error(f"Print generation failed: {resp.text}")
                except Exception as e:
                    st.error(f"Error: {e}")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Sidebar
    st.sidebar.title("🎨 Gemini Studio")
    st.sidebar.markdown("### Professional Print-on-Demand Workflow")
    
    # API status
    try:
        health = requests.get(f"{API_URL}/api/health", timeout=3)
        if health.status_code == 200:
            st.sidebar.success("🟢 API Connected")
        else:
            st.sidebar.error("🔴 API Error")
    except:
        st.sidebar.warning("🟡 API Offline")
    
    # Navigation
    tab_names = ["🔍 Search", "🎨 Studio", "👕 Mockup", "📦 Export"]
    tabs = st.tabs(tab_names)
    
    with tabs[0]:
        search_tab()
    
    with tabs[1]:
        studio_tab()
    
    with tabs[2]:
        mockup_tab()
    
    with tabs[3]:
        export_tab()
    
    # Footer
    st.sidebar.divider()
    st.sidebar.caption("Powered by Moonshine Print Studio API")
    st.sidebar.caption("Version 2.1.0 | Vercel Deployment")

# ============================================================================
# RUN APP
# ============================================================================
if __name__ == "__main__":
    main()
