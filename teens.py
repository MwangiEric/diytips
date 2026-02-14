import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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
FALLBACK_COLOR = (30, 41, 59)  # dark indigo

# ----------------------------
#  TEMPLATES – clean visual variations
# ----------------------------
TEMPLATES = {
    "Classic": {
        "box": True,
        "box_opacity": 180,
        "border_color": (79, 70, 229),      # indigo
        "text_color": (255, 255, 255),
        "author_color": (124, 58, 237),      # violet
        "author_position": "bottom_right",
        "logo_position": "top_center",
        "description": "Centered box • Colored border • Top logo"
    },
    "Minimal": {
        "box": False,
        "text_color": (255, 255, 255),
        "author_color": (200, 200, 200),
        "author_position": "bottom_center",
        "logo_position": "top_left",
        "description": "No box • Text on background • Small logo top‑left"
    },
    "Bold": {
        "box": True,
        "box_opacity": 220,
        "border_color": (236, 72, 153),      # pink
        "text_color": (255, 255, 255),
        "author_color": (236, 72, 153),
        "author_position": "inside_bottom",
        "logo_position": "top_center",
        "description": "Dark box • Pink accents • Author inside box"
    },
    "Light": {
        "box": True,
        "box_opacity": 200,
        "border_color": (255, 255, 255),
        "text_color": (30, 41, 59),          # dark text on light box
        "author_color": (79, 70, 229),
        "author_position": "bottom_right",
        "logo_position": "top_center",
        "description": "White box • Dark text • Clean & bright"
    }
}

# ----------------------------
#  SIMPLE FONT LOADING
# ----------------------------
@st.cache_resource
def get_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
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
#  GROQ KEYWORDS
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
    except:
        words = quote.lower().split()[:5]
        return [w.strip(",.!?;:") for w in words if len(w) > 3][:5]

# ----------------------------
#  MOON SHINE BACKGROUND
# ----------------------------
@st.cache_data(ttl=3600)
def fetch_background_image(keywords):
    query = " ".join(keywords) if keywords else "abstract"
    try:
        params = {"q": query, "t": "backgrounds", "w": 1080}
        resp = requests.get(MOONSHINE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        assets = data.get("results", {}).get("assets", [])
        if assets:
            img_url = assets[0]["img_url"]
            img_resp = requests.get(img_url, timeout=15)
            img = Image.open(BytesIO(img_resp.content)).convert("RGB")
            return img.resize((W, H), Image.Resampling.LANCZOS)
    except Exception as e:
        st.warning(f"Background fetch failed: {e}. Using solid color.")
    return None

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
#  VIDEO GENERATION (template‑aware)
# ----------------------------
def generate_quote_video(quote, author, template_name, use_dynamic_bg=True):
    """Generate MP4 with selected template."""
    logo = load_logo()
    font_quote = get_font(52)
    font_author = get_font(42)
    tmpl = TEMPLATES[template_name]

    # Background
    if use_dynamic_bg:
        keywords = get_keywords_from_quote(quote)
        bg_img = fetch_background_image(keywords)
    else:
        bg_img = None
    if bg_img is None:
        bg_img = Image.new("RGB", (W, H), FALLBACK_COLOR)

    # Static base layer
    base = bg_img.copy()
    draw = ImageDraw.Draw(base)

    # ----- LOGO -----
    if tmpl["logo_position"] == "top_center":
        base.paste(logo, ((W - logo.width)//2, 60), logo)
    elif tmpl["logo_position"] == "top_left":
        base.paste(logo, (40, 40), logo)

    # ----- BOX (optional) -----
    box_w, box_h = int(W * 0.8), int(H * 0.55)
    box_x, box_y = (W - box_w)//2, (H - box_h)//2

    if tmpl["box"]:
        # Shadow
        draw.rounded_rectangle(
            [box_x+8, box_y+8, box_x+box_w+8, box_y+box_h+8],
            radius=25, fill=(0,0,0,80)
        )
        # Main box
        fill_color = (0, 0, 0, tmpl["box_opacity"])  # always dark overlay
        draw.rounded_rectangle(
            [box_x, box_y, box_x+box_w, box_y+box_h],
            radius=25, fill=fill_color,
            outline=tmpl.get("border_color"), width=4
        )

    base_array = np.array(base)

    def make_frame(t):
        img = Image.fromarray(base_array.copy())
        draw = ImageDraw.Draw(img)

        # ----- TYPEWRITER QUOTE -----
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
                # No box – vertically center on whole canvas
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

        # ----- AUTHOR (fade‑in last 2 seconds) -----
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
#  PREVIEW IMAGE (template‑aware)
# ----------------------------
def generate_preview(quote, author, template_name):
    logo = load_logo()
    font_quote = get_font(48)
    font_author = get_font(36)
    tmpl = TEMPLATES[template_name]

    # Preview uses fallback color for consistency
    img = Image.new("RGB", (800, 1200), FALLBACK_COLOR)
    draw = ImageDraw.Draw(img)

    # Logo
    logo_small = logo.resize((160, 52))
    if tmpl["logo_position"] == "top_center":
        img.paste(logo_small, ((800 - logo_small.width)//2, 40), logo_small)
    elif tmpl["logo_position"] == "top_left":
        img.paste(logo_small, (30, 30), logo_small)

    # Box dimensions for preview (scaled down)
    box_w, box_h = 640, 500
    box_x, box_y = 80, 300

    if tmpl["box"]:
        draw.rounded_rectangle([box_x+5, box_y+5, box_x+box_w+5, box_y+box_h+5],
                               radius=20, fill=(0,0,0,60))
        draw.rounded_rectangle([box_x, box_y, box_x+box_w, box_y+box_h],
                               radius=20, fill=(0,0,0,tmpl["box_opacity"]),
                               outline=tmpl.get("border_color"), width=3)

    # Quote text
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

    # Author
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

    st.markdown("<h1 style='text-align:center; color:#4F46E5;'>✨ Quote Video Studio</h1>",
                unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#666;'>Groq keywords • Moon Shine backgrounds • 4 templates</p>",
                unsafe_allow_html=True)

    with st.sidebar:
        st.image(load_logo(), use_column_width=True)
        st.markdown("---")

        # Template selector
        st.subheader("🎨 Template")
        template_name = st.selectbox(
            "Choose style",
            list(TEMPLATES.keys()),
            format_func=lambda x: f"{x} – {TEMPLATES[x]['description']}"
        )

        st.markdown("---")
        st.subheader("🖼️ Background")
        use_dynamic = st.checkbox("Use AI‑generated background", value=True,
                                  help="Groq extracts keywords → Moon Shine fetches matching image")
        st.caption("Requires `groq_key` in secrets")

        st.markdown("---")
        st.caption("Moon Shine API provides free‑to‑use background images")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("✍️ Quote")
        default_quote = "Mental health is not a destination, but a process. It's about how you drive, not where you're going."
        quote = st.text_area("Quote text", default_quote, height=120)

        col_a, col_b = st.columns(2)
        with col_a:
            author_name = st.text_input("Author", "Jane Kariuki")
        with col_b:
            author_title = st.text_input("Title", "Clinical Psychologist")
        full_author = f"{author_name}, {author_title}" if author_title else author_name

        st.caption(f"**{len(quote)}** characters – best under 400")

        if st.button("🎬 Generate 10s Video", type="primary", use_container_width=True):
            if not quote:
                st.error("Please enter a quote.")
            elif len(quote) > 500:
                st.error("Quote too long – max 500 characters.")
            else:
                with st.spinner("🔍 Extracting keywords + fetching background..." if use_dynamic else "Rendering video..."):
                    path = generate_quote_video(
                        quote, full_author, template_name,
                        use_dynamic_bg=use_dynamic
                    )
                    with open(path, "rb") as f:
                        video_bytes = f.read()
                st.success("✅ Video ready!")
                st.video(video_bytes)
                st.download_button("💾 Download MP4", video_bytes,
                                   file_name=f"{template_name}_{datetime.now():%Y%m%d_%H%M%S}.mp4",
                                   mime="video/mp4",
                                   use_container_width=True)

    with col2:
        st.subheader("💡 Preview")
        if st.button("🖼️ Show Preview", use_container_width=True):
            if quote:
                preview = generate_preview(quote, full_author, template_name)
                st.image(preview, use_column_width=True)
                buf = BytesIO()
                preview.save(buf, format="PNG")
                st.download_button("📥 Download Preview", buf.getvalue(),
                                   file_name=f"{template_name}_preview.png",
                                   mime="image/png")
        else:
            st.info("👈 Enter a quote and click 'Show Preview'")

if __name__ == "__main__":
    main()