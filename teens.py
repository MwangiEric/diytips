import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import moviepy.editor as mpy
import numpy as np
from io import BytesIO
import tempfile
import uuid
from datetime import datetime
import requests
import json

# ----------------------------
#  CONSTANTS
# ----------------------------
W, H = 1080, 1920
DURATION = 10
FPS = 24
MOONSHINE_URL = "https://moon-shine.vercel.app/api/search"
FALLBACK_COLOR = (30, 41, 59)

# ----------------------------
#  FONT LOADING (robust)
# ----------------------------
@st.cache_resource
def get_font(size):
    """Try common system fonts, fallback to default."""
    font_paths = [
        "arial.ttf",
        "Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "/System/Library/Fonts/Arial.ttf",                 # macOS
        "C:/Windows/Fonts/arial.ttf"                       # Windows
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()

# ----------------------------
#  LOGO
# ----------------------------
@st.cache_data
def load_logo():
    try:
        r = requests.get("https://ik.imagekit.io/ericmwangi/cropped-Parenteen-Kenya-Logo-rec.png", timeout=5)
        return Image.open(BytesIO(r.content)).convert("RGBA").resize((200, 64))
    except:
        logo = Image.new("RGBA", (250, 80), (0,0,0,0))
        d = ImageDraw.Draw(logo)
        d.text((20,20), "PARENTEEN", fill="#4F46E5", font=get_font(28))
        d.text((20,50), "KENYA", fill="#7C3AED", font=get_font(28))
        return logo.resize((200, 64))

# ----------------------------
#  GROQ KEYWORD EXTRACTION
# ----------------------------
def get_keywords_from_quote(quote):
    try:
        from groq import Groq
        client = Groq(api_key=st.secrets["groq_key"])
        prompt = f"""Extract 3 to 5 concrete, visual keywords from this quote. 
Only return a JSON array of strings, nothing else.
Quote: "{quote}"
Keywords:"""
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("keywords", [])[:5]
    except Exception as e:
        st.warning(f"Keyword extraction failed: {e}. Using fallback.")
        words = quote.lower().split()[:5]
        return [w.strip(",.!?;:") for w in words if len(w) > 3][:5]

# ----------------------------
#  MOON SHINE API – SEARCH
# ----------------------------
@st.cache_data(ttl=600)  # 10 minutes cache
def search_moonshine(query):
    """Return list of asset dicts from Moon Shine."""
    try:
        params = {"q": query, "t": "backgrounds", "w": 1080}
        resp = requests.get(MOONSHINE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", {}).get("assets", [])
    except Exception as e:
        st.error(f"Search failed: {e}")
        return []

# ----------------------------
#  FETCH FULL IMAGE BY URL
# ----------------------------
@st.cache_data(ttl=3600)
def fetch_image_from_url(url):
    """Download image from URL and return PIL Image (RGB, resized to W×H)."""
    try:
        resp = requests.get(url, timeout=15)
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        return img.resize((W, H), Image.Resampling.LANCZOS)
    except Exception as e:
        st.warning(f"Failed to load image: {e}")
        return None

# ----------------------------
#  TEMPLATES (unchanged)
# ----------------------------
TEMPLATES = {
    "Classic": {
        "box": True, "box_opacity": 180, "border_color": (79,70,229),
        "text_color": (255,255,255), "author_color": (124,58,237),
        "author_position": "bottom_right", "logo_position": "top_center",
        "description": "Centered box • Colored border • Top logo"
    },
    "Minimal": {
        "box": False, "text_color": (255,255,255), "author_color": (200,200,200),
        "author_position": "bottom_center", "logo_position": "top_left",
        "description": "No box • Text on background • Small logo top‑left"
    },
    "Bold": {
        "box": True, "box_opacity": 220, "border_color": (236,72,153),
        "text_color": (255,255,255), "author_color": (236,72,153),
        "author_position": "inside_bottom", "logo_position": "top_center",
        "description": "Dark box • Pink accents • Author inside box"
    },
    "Light": {
        "box": True, "box_opacity": 200, "border_color": (255,255,255),
        "text_color": (30,41,59), "author_color": (79,70,229),
        "author_position": "bottom_right", "logo_position": "top_center",
        "description": "White box • Dark text • Clean & bright"
    }
}

# ----------------------------
#  TEXT WRAPPING
# ----------------------------
def wrap_text(text, font, max_width):
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines

# ----------------------------
#  VIDEO GENERATION
# ----------------------------
def generate_quote_video(quote, author, template_name, bg_image=None):
    """Generate MP4 with optional background image (PIL RGB, resized to W×H)."""
    logo = load_logo()
    font_quote = get_font(52)
    font_author = get_font(42)
    tmpl = TEMPLATES[template_name]

    # Use provided bg_image or fallback color
    if bg_image is None:
        bg_image = Image.new("RGB", (W, H), FALLBACK_COLOR)

    # Static base layer
    base = bg_image.copy()
    draw = ImageDraw.Draw(base)

    # Logo
    if tmpl["logo_position"] == "top_center":
        base.paste(logo, ((W - logo.width)//2, 60), logo)
    elif tmpl["logo_position"] == "top_left":
        base.paste(logo, (40, 40), logo)

    # Box (optional)
    box_w, box_h = int(W * 0.8), int(H * 0.55)
    box_x, box_y = (W - box_w)//2, (H - box_h)//2

    if tmpl["box"]:
        # Shadow
        draw.rounded_rectangle(
            [box_x+8, box_y+8, box_x+box_w+8, box_y+box_h+8],
            radius=25, fill=(0,0,0,80)
        )
        # Main box
        fill_color = (0, 0, 0, tmpl["box_opacity"])
        draw.rounded_rectangle(
            [box_x, box_y, box_x+box_w, box_y+box_h],
            radius=25, fill=fill_color,
            outline=tmpl.get("border_color"), width=4
        )

    base_array = np.array(base)

    def make_frame(t):
        img = Image.fromarray(base_array.copy())
        draw = ImageDraw.Draw(img)

        # Typewriter quote
        reveal_time = 7
        chars = int(len(quote) * min(t / reveal_time, 1.0))
        visible = quote[:chars]
        if visible:
            lines = wrap_text(visible, font_quote, box_w - 80)
            line_spacing = 65
            total_h = len(lines) * line_spacing

            if tmpl["box"]:
                start_y = box_y + (box_h - total_h) // 2
            else:
                start_y = (H - total_h) // 2

            for i, line in enumerate(lines):
                bbox = font_quote.getbbox(line)
                line_w = bbox[2] - bbox[0]
                if tmpl["box"]:
                    x = box_x + (box_w - line_w) // 2
                else:
                    x = (W - line_w) // 2
                y = start_y + i * line_spacing
                # Shadow
                draw.text((x+2, y+2), line, font=font_quote, fill=(0,0,0,160))
                draw.text((x, y), line, font=font_quote, fill=tmpl["text_color"])

        # Author fade‑in
        if t >= 8:
            alpha = int(255 * min((t - 8) / 2, 1.0))
            author_text = f"— {author}"
            bbox = font_author.getbbox(author_text)
            author_w = bbox[2] - bbox[0]

            if tmpl["author_position"] == "bottom_right":
                x = box_x + box_w - author_w - 40 if tmpl["box"] else W - author_w - 60
                y = box_y + box_h - 70 if tmpl["box"] else H - 120
            elif tmpl["author_position"] == "bottom_center":
                x = (W - author_w) // 2
                y = H - 140
            elif tmpl["author_position"] == "inside_bottom":
                x = box_x + box_w - author_w - 40
                y = box_y + box_h - 70

            draw.text((x, y), author_text, font=font_author,
                     fill=(*tmpl["author_color"], alpha))

        return np.array(img)

    clip = mpy.VideoClip(make_frame, duration=DURATION)
    temp_dir = tempfile.mkdtemp()
    out_path = f"{temp_dir}/quote_{uuid.uuid4().hex}.mp4"
    clip.write_videofile(out_path, fps=FPS, codec="libx264", audio=False,
                         ffmpeg_params=["-preset", "fast", "-crf", "23"],
                         logger=None)
    return out_path

# ----------------------------
#  PREVIEW IMAGE
# ----------------------------
def generate_preview(quote, author, template_name):
    logo = load_logo()
    font_quote = get_font(48)
    font_author = get_font(36)
    tmpl = TEMPLATES[template_name]

    img = Image.new("RGB", (800, 1200), FALLBACK_COLOR)
    draw = ImageDraw.Draw(img)

    logo_small = logo.resize((160, 52))
    if tmpl["logo_position"] == "top_center":
        img.paste(logo_small, ((800 - logo_small.width)//2, 40), logo_small)
    elif tmpl["logo_position"] == "top_left":
        img.paste(logo_small, (30, 30), logo_small)

    box_w, box_h = 640, 500
    box_x, box_y = 80, 300

    if tmpl["box"]:
        draw.rounded_rectangle([box_x+5, box_y+5, box_x+box_w+5, box_y+box_h+5],
                               radius=20, fill=(0,0,0,60))
        draw.rounded_rectangle([box_x, box_y, box_x+box_w, box_y+box_h],
                               radius=20, fill=(0,0,0,tmpl["box_opacity"]),
                               outline=tmpl.get("border_color"), width=3)

    lines = wrap_text(quote, font_quote, box_w - 60)
    line_h = 60
    total_h = len(lines) * line_h

    if tmpl["box"]:
        start_y = box_y + (box_h - total_h) // 2
    else:
        start_y = (1200 - total_h) // 2

    for i, line in enumerate(lines):
        bbox = font_quote.getbbox(line)
        line_w = bbox[2] - bbox[0]
        if tmpl["box"]:
            x = box_x + (box_w - line_w) // 2
        else:
            x = (800 - line_w) // 2
        y = start_y + i * line_h
        draw.text((x+1, y+1), line, font=font_quote, fill=(0,0,0,100))
        draw.text((x, y), line, font=font_quote, fill=tmpl["text_color"])

    author_text = f"— {author}"
    bbox = font_author.getbbox(author_text)
    author_w = bbox[2] - bbox[0]

    if tmpl["author_position"] == "bottom_right":
        x = box_x + box_w - author_w - 30 if tmpl["box"] else 800 - author_w - 40
        y = box_y + box_h - 50 if tmpl["box"] else 1150
    elif tmpl["author_position"] == "bottom_center":
        x = (800 - author_w) // 2
        y = 1150
    elif tmpl["author_position"] == "inside_bottom":
        x = box_x + box_w - author_w - 30
        y = box_y + box_h - 50

    draw.text((x, y), author_text, font=font_author, fill=tmpl["author_color"])
    return img

# ----------------------------
#  STREAMLIT UI
# ----------------------------
def main():
    st.set_page_config(page_title="Quote Video Studio", page_icon="✨", layout="wide")
    st.markdown("<h1 style='text-align:center; color:#4F46E5;'>✨ Quote Video Studio</h1>", unsafe_allow_html=True)

    # Initialize session state
    if "keywords" not in st.session_state:
        st.session_state.keywords = []
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "selected_img_url" not in st.session_state:
        st.session_state.selected_img_url = None

    with st.sidebar:
        st.image(load_logo(), use_column_width=True)
        st.markdown("---")
        template_name = st.selectbox("🎨 Template", list(TEMPLATES.keys()),
                                     format_func=lambda x: f"{x} – {TEMPLATES[x]['description']}")
        st.markdown("---")
        st.caption("Moon Shine API • Groq AI • System fonts")

    # Main area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("✍️ Quote")
        quote = st.text_area("Quote text", height=120,
                             value="Mental health is not a destination, but a process. It's about how you drive, not where you're going.")
        col_a, col_b = st.columns(2)
        with col_a:
            author_name = st.text_input("Author", "Jane Kariuki")
        with col_b:
            author_title = st.text_input("Title", "Clinical Psychologist")
        full_author = f"{author_name}, {author_title}" if author_title else author_name

        # Search section
        st.markdown("---")
        st.subheader("🔍 Background Search")

        if st.button("🎯 Generate Keywords & Search", use_container_width=True):
            with st.spinner("Extracting keywords..."):
                kw = get_keywords_from_quote(quote)
                st.session_state.keywords = kw
            with st.spinner("Searching Moon Shine..."):
                results = search_moonshine(" ".join(kw))
                st.session_state.search_results = results
                st.session_state.selected_img_url = None  # reset selection

        # Editable keywords
        if st.session_state.keywords:
            col_kw1, col_kw2 = st.columns([3, 1])
            with col_kw1:
                kw_str = st.text_input("Edit keywords", value=" ".join(st.session_state.keywords))
            with col_kw2:
                if st.button("Search", key="re_search"):
                    with st.spinner("Searching..."):
                        results = search_moonshine(kw_str)
                        st.session_state.search_results = results
                        st.session_state.keywords = kw_str.split()
                        st.session_state.selected_img_url = None

        # Display thumbnails
        if st.session_state.search_results:
            st.markdown("### Select a background")
            assets = st.session_state.search_results
            # Show in rows of 3
            rows = [assets[i:i+3] for i in range(0, len(assets), 3)]
            for row in rows:
                cols = st.columns(3)
                for idx, asset in enumerate(row):
                    with cols[idx]:
                        thumb_url = asset.get("thumbnail_src") or asset.get("img_url")
                        if thumb_url:
                            st.image(thumb_url, use_container_width=True)
                        else:
                            st.caption("No thumbnail")
                        if st.button("Select", key=f"sel_{asset['img_url']}"):
                            st.session_state.selected_img_url = asset["img_url"]
                            st.rerun()  # to update preview

        # Show selected image preview
        if st.session_state.selected_img_url:
            st.markdown("---")
            st.success("✅ Background selected")
            # Optionally show small preview
            try:
                img = fetch_image_from_url(st.session_state.selected_img_url)
                if img:
                    st.image(img.resize((200, 356)), caption="Selected background")
            except:
                pass

        # Generate video button
        st.markdown("---")
        if st.button("🎬 Generate 10s Video", type="primary", use_container_width=True):
            if not quote:
                st.error("Please enter a quote.")
            elif len(quote) > 500:
                st.error("Quote too long – max 500 characters.")
            else:
                # Load background image if selected
                bg_image = None
                if st.session_state.selected_img_url:
                    bg_image = fetch_image_from_url(st.session_state.selected_img_url)
                with st.spinner("Rendering video..."):
                    path = generate_quote_video(quote, full_author, template_name, bg_image)
                    with open(path, "rb") as f:
                        video_bytes = f.read()
                st.success("✅ Video ready!")
                st.video(video_bytes)
                st.download_button("💾 Download MP4", video_bytes,
                                   file_name=f"{template_name}_{datetime.now():%Y%m%d_%H%M%S}.mp4",
                                   mime="video/mp4", use_container_width=True)

    with col2:
        st.subheader("💡 Preview")
        if st.button("🖼️ Show Preview", use_container_width=True):
            if quote:
                preview = generate_preview(quote, full_author, template_name)
                st.image(preview, use_container_width=True)
                buf = BytesIO()
                preview.save(buf, format="PNG")
                st.download_button("📥 Download Preview", buf.getvalue(),
                                   file_name=f"{template_name}_preview.png", mime="image/png")
        else:
            st.info("👈 Enter a quote and click 'Show Preview'")

if __name__ == "__main__":
    main()