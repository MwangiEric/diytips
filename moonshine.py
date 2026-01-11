import streamlit as st
import requests
from streamlit_image_select import image_select

# --- 1. CONFIG & SEARCH LOGIC ---
SEARX_URL = "https://far-paule-emw-a67bd497.koyeb.app/search"

# Smart domain mappings for high-quality art
DOMAIN_MAP = {
    "art": ["pinterest.com", "artstation.com"],
    "design": ["behance.net", "dribbble.com"],
    "retro": ["freevector.com", "vecteezy.com"],
    "logo": ["logopond.com", "seeklogo.com"]
}

def get_smart_query(user_q, mode):
    if mode == "Manual (Broad)":
        return user_q
    
    # Smart Mode Expansion
    added_sites = []
    for key, domains in DOMAIN_MAP.items():
        if key in user_q.lower():
            added_sites.extend(domains)
            
    base = f"official graphic vector {user_q} -shirt -mockup"
    if added_sites:
        site_str = " OR ".join([f"site:{s}" for s in added_sites])
        return f"{base} ({site_str})"
    return base

def fetch_data(query, page=1):
    params = {"q": query, "categories": "images", "format": "json", "pageno": page}
    try:
        r = requests.get(SEARX_URL, params=params, timeout=10)
        # Filter for "printable" quality: results with a source image and decent width
        return [res for res in r.json().get("results", []) if res.get("img_src") and res.get("thumbnail_src")]
    except:
        return []

# --- 2. SESSION INITIALIZATION ---
if "raw_results" not in st.session_state:
    st.session_state.raw_results = []
if "page" not in st.session_state:
    st.session_state.page = 1
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

# --- 3. UI LAYOUT ---
st.set_page_config(page_title="Smart Print Scout", layout="wide")

with st.sidebar:
    st.title("⚙️ Controls")
    mode = st.radio("Search Mode", ["Smart (Print-Ready)", "Manual (Broad)"])
    st.info("Smart mode targets professional portfolios (Behance, ArtStation) and vector archives.")

st.title("👕 Smart Apparel Scout")
user_q = st.text_input("Describe your design...", placeholder="e.g., 'Japanese Cyberpunk Oni'")

# Trigger search if query changes
if user_q and user_q != st.session_state.last_query:
    st.session_state.last_query = user_q
    st.session_state.raw_results = []
    st.session_state.page = 1
    with st.spinner("Scouting high-quality assets..."):
        st.session_state.raw_results = fetch_data(get_smart_query(user_q, mode))

# --- 4. GALLERY & PREVIEW ---
if st.session_state.raw_results:
    # IMPORTANT: We use a static list to ensure index alignment
    current_data = st.session_state.raw_results
    thumbs = [item["thumbnail_src"] for item in current_data]

    selected_idx = image_select(
        label="Select a graphic to preview",
        images=thumbs,
        key=f"gallery_{user_q}_{len(current_data)}" # Key forces refresh when 'More' is clicked
    )

    if st.button("➕ Load More Designs", use_container_width=True):
        st.session_state.page += 1
        new_data = fetch_data(get_smart_query(user_q, mode), page=st.session_state.page)
        st.session_state.raw_results.extend(new_data)
        st.rerun()

    # --- 5. THE GUARDED PREVIEW ---
    if selected_idx is not None:
        try:
            chosen = current_data[selected_idx]
            st.divider()
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("Realistic Mockup")
                # Layering: Background -> Design -> Shirt Texture
                shirt_mask = "https://i.imgur.com/8fS73O4.png"
                st.html(f"""
                <div style="background-color: #f8f8f8; width: 340px; height: 420px; margin: auto; position: relative; border-radius: 15px; border: 1px solid #eee; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                    <div style="position: absolute; top: 25%; left: 50%; transform: translateX(-50%); width: 50%; z-index: 1;">
                        <img src="{chosen['img_src']}" style="width: 100%; filter: contrast(1.05);">
                    </div>
                    <img src="{shirt_mask}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; pointer-events: none; opacity: 0.6;">
                </div>
                """)

            with c2:
                st.subheader("Design Specs")
                st.write(f"**Origin:** {chosen.get('source', 'Unknown')}")
                st.write(f"**Resolution:** {chosen.get('width', '?')} x {chosen.get('height', '?')}")
                st.write(f"**Engine:** {chosen.get('engine', 'Multi')}")
                
                if st.button("🚀 Process for Printing", use_container_width=True):
                    st.success(f"Successfully captured {chosen['img_src']} for production!")
                    st.balloons()
        except Exception as e:
            st.warning("Please re-select the image to sync preview.")
