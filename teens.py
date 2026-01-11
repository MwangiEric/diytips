import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import moviepy.editor as mpy
from moviepy.editor import *
from io import BytesIO
import tempfile
import uuid
import random
from datetime import datetime

# ==================== CACHED GENERATION ====================
@st.cache_data(ttl=3600, show_spinner=False)
def generate_quote_video_cached(quote_text, author_name, bg_type="particles"):
    """Generate video with caching (no audio)"""
    return generate_quote_video(quote_text, author_name, bg_type)

# ==================== BRAND COLORS ====================
BRAND_COLORS = {
    "primary": "#4F46E5",     # Indigo
    "secondary": "#7C3AED",   # Violet
    "accent": "#EC4899",      # Pink
    "light": "#8B5CF6",       # Light purple
    "dark": "#3730A3",        # Dark blue
    "text": "#1F2937",        # Gray-800
    "bg": "#F9FAFB",          # Gray-50
    "quote_box": "#FFFFFF"    # White for quote box
}

# ==================== QUOTE PREVIEW GENERATOR ====================
def generate_quote_preview(quote_text, author_name):
    """Generate static preview image of quote"""
    W, H = 800, 1000  # Preview size
    
    # Create base image
    img = Image.new('RGB', (W, H), color=BRAND_COLORS["bg"])
    draw = ImageDraw.Draw(img)
    
    # Add subtle gradient background
    for y in range(0, H, 2):
        ratio = y / H
        r = int(249 * (1 - ratio) + 79 * ratio)
        g = int(250 * (1 - ratio) + 70 * ratio)
        b = int(251 * (1 - ratio) + 229 * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b), width=2)
    
    # Create quote box
    box_width = int(W * 0.85)
    box_height = int(H * 0.7)
    box_x = (W - box_width) // 2
    box_y = (H - box_height) // 2
    
    # Shadow effect
    shadow_offset = 10
    draw.rounded_rectangle(
        [box_x+shadow_offset, box_y+shadow_offset, 
         box_x+box_width+shadow_offset, box_y+box_height+shadow_offset],
        radius=30,
        fill="#00000020"
    )
    
    # Main box with gradient border
    for i in range(8):
        color_ratio = i / 8
        r = int(79 * (1 - color_ratio) + 255 * color_ratio)
        g = int(70 * (1 - color_ratio) + 255 * color_ratio)
        b = int(229 * (1 - color_ratio) + 255 * color_ratio)
        draw.rounded_rectangle(
            [box_x+i, box_y+i, box_x+box_width-i, box_y+box_height-i],
            radius=30-i//2,
            outline=(r, g, b),
            width=1
        )
    
    # Fill box
    draw.rounded_rectangle(
        [box_x+8, box_y+8, box_x+box_width-8, box_y+box_height-8],
        radius=25,
        fill=BRAND_COLORS["quote_box"]
    )
    
    # Load font
    try:
        # Try different fonts
        fonts_to_try = ["arial.ttf", "arialbd.ttf", "times.ttf", "verdana.ttf"]
        quote_font = None
        for font_name in fonts_to_try:
            try:
                quote_font = ImageFont.truetype(font_name, 42)
                break
            except:
                continue
        if not quote_font:
            quote_font = ImageFont.load_default()
        
        title_font = ImageFont.truetype(font_name, 36) if quote_font else ImageFont.load_default()
        author_font = ImageFont.truetype(font_name, 32) if quote_font else ImageFont.load_default()
    except:
        quote_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        author_font = ImageFont.load_default()
    
    # Add title
    title = "QUOTE"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = bbox[2] - bbox[0]
    draw.text(
        ((W - title_width) // 2, box_y - 60),
        title,
        font=title_font,
        fill=BRAND_COLORS["primary"],
        stroke_width=2,
        stroke_fill=BRAND_COLORS["light"]
    )
    
    # Split quote into lines
    max_chars_per_line = 40
    words = quote_text.split()
    lines = []
    current_line = []
    
    for word in words:
        if len(' '.join(current_line + [word])) <= max_chars_per_line:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw quote lines
    line_height = 60
    start_y = box_y + 80
    
    for i, line in enumerate(lines):
        # Center each line
        bbox = draw.textbbox((0, 0), line, font=quote_font)
        text_width = bbox[2] - bbox[0]
        x = (W - text_width) // 2
        y = start_y + i * line_height
        
        # Text shadow
        draw.text((x+2, y+2), line, font=quote_font, fill="#00000030")
        # Main text
        draw.text((x, y), line, font=quote_font, fill=BRAND_COLORS["text"])
    
    # Add author
    author_text = f"— {author_name}"
    bbox = draw.textbbox((0, 0), author_text, font=author_font)
    text_width = bbox[2] - bbox[0]
    author_x = box_x + box_width - text_width - 40
    author_y = box_y + box_height - 60
    
    draw.text((author_x+2, author_y+2), author_text, font=author_font, fill="#00000030")
    draw.text((author_x, author_y), author_text, font=author_font, fill=BRAND_COLORS["primary"])
    
    # Add decorative elements
    # Top-left and bottom-right corners
    corner_size = 30
    # Top-left
    draw.arc([box_x-15, box_y-15, box_x+corner_size, box_y+corner_size], 
             180, 270, fill=BRAND_COLORS["accent"], width=3)
    # Bottom-right
    draw.arc([box_x+box_width-corner_size, box_y+box_height-corner_size, 
              box_x+box_width+15, box_y+box_height+15], 
             0, 90, fill=BRAND_COLORS["accent"], width=3)
    
    # Add watermark
    watermark = "Parenteen Kenya"
    bbox = draw.textbbox((0, 0), watermark, font=author_font)
    watermark_width = bbox[2] - bbox[0]
    draw.text(
        (W - watermark_width - 20, H - 40),
        watermark,
        font=author_font,
        fill=BRAND_COLORS["light"] + "80"
    )
    
    return img

# ==================== PARTICLE SYSTEM ====================
class Particle:
    def __init__(self, width, height):
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        self.size = random.randint(2, 6)
        self.speed_x = random.uniform(-0.8, 0.8)
        self.speed_y = random.uniform(-0.8, 0.8)
        self.color = random.choice([
            BRAND_COLORS["primary"],
            BRAND_COLORS["secondary"],
            BRAND_COLORS["accent"],
            BRAND_COLORS["light"]
        ])
        self.life = random.randint(80, 150)
        self.alpha = random.randint(100, 200)

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.life -= 1
        if self.life <= 0:
            return False
        # Fade out
        if self.life < 30:
            self.alpha = int(self.alpha * (self.life / 30))
        return True

# ==================== VIDEO GENERATION (NO AUDIO) ====================
def generate_quote_video(quote_text, author_name, bg_type="particles"):
    """Generate 10-second quote video WITHOUT audio"""
    # Video settings
    W, H = 1080, 1920  # Vertical format
    DURATION = 10
    FPS = 24
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Generate frames
    frames = []
    
    for i in range(DURATION * FPS):
        # Time progress
        t = i / FPS
        
        # Create base image
        img = Image.new('RGB', (W, H), color=BRAND_COLORS["bg"])
        draw = ImageDraw.Draw(img)
        
        # ===== BACKGROUND =====
        if bg_type == "particles":
            # Generate particles every 3 frames
            if i == 0 or i % 3 == 0:
                particles = [Particle(W, H) for _ in range(25)]  # Reduced for performance
            
            # Draw particles
            for p in particles[:]:  # Copy list for safe removal
                if not p.update():
                    particles.remove(p)
                else:
                    # Create semi-transparent particle
                    particle_img = Image.new('RGBA', (p.size*2, p.size*2), (0, 0, 0, 0))
                    particle_draw = ImageDraw.Draw(particle_img)
                    r, g, b = int(p.color[1:3], 16), int(p.color[3:5], 16), int(p.color[5:7], 16)
                    particle_draw.ellipse([0, 0, p.size*2, p.size*2], 
                                        fill=(r, g, b, p.alpha))
                    img.paste(particle_img, (int(p.x)-p.size, int(p.y)-p.size), particle_img)
        
        elif bg_type == "gradient":
            # Animated gradient
            offset = int(t * 50) % H
            for y in range(0, H, 2):
                ratio = ((y + offset) % H) / H
                r = int(79 * (1 - ratio) + 249 * ratio)
                g = int(70 * (1 - ratio) + 250 * ratio)
                b = int(229 * (1 - ratio) + 251 * ratio)
                draw.line([(0, y), (W, y)], fill=(r, g, b), width=2)
        
        elif bg_type == "waves":
            # Wave pattern
            for x in range(0, W, 20):
                wave_y = H//2 + int(100 * np.sin(x/100 + t * 2))
                draw.line([(x, wave_y), (x+10, wave_y)], 
                         fill=BRAND_COLORS["light"], width=3)
        
        # ===== QUOTE BOX =====
        box_width = int(W * 0.82)
        box_height = int(H * 0.65)
        box_x = (W - box_width) // 2
        box_y = (H - box_height) // 2
        
        # Animated shadow (grows over time)
        shadow_size = int(10 + 5 * np.sin(t * 2))
        draw.rounded_rectangle(
            [box_x+shadow_size, box_y+shadow_size, 
             box_x+box_width+shadow_size, box_y+box_height+shadow_size],
            radius=35,
            fill="#00000020"
        )
        
        # Animated border (color cycle)
        border_color_index = int(t * 2) % 3
        border_colors = [BRAND_COLORS["primary"], BRAND_COLORS["secondary"], BRAND_COLORS["accent"]]
        
        # Main box
        draw.rounded_rectangle(
            [box_x, box_y, box_x+box_width, box_y+box_height],
            radius=35,
            fill=BRAND_COLORS["quote_box"],
            outline=border_colors[border_color_index],
            width=5
        )
        
        # Inner glow
        draw.rounded_rectangle(
            [box_x+3, box_y+3, box_x+box_width-3, box_y+box_height-3],
            radius=32,
            outline=border_colors[border_color_index] + "30",
            width=2
        )
        
        # ===== TYPEWRITER ANIMATION =====
        try:
            quote_font = ImageFont.truetype("arial.ttf", 52)
            author_font = ImageFont.truetype("arial.ttf", 40)
        except:
            quote_font = ImageFont.load_default()
            author_font = ImageFont.load_default()
        
        # Calculate reveal
        total_chars = len(quote_text)
        reveal_time = 7  # 7 seconds to reveal all text
        chars_to_show = min(int((t / reveal_time) * total_chars), total_chars)
        visible_text = quote_text[:chars_to_show]
        
        # Split into lines
        lines = []
        words = visible_text.split()
        current_line = ""
        max_line_width = box_width * 0.9
        
        for word in words:
            test_line = f"{current_line} {word}".strip() if current_line else word
            # Approximate width
            test_bbox = draw.textbbox((0, 0), test_line, font=quote_font)
            test_width = test_bbox[2] - test_bbox[0]
            
            if test_width < max_line_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Draw lines with typewriter effect
        line_height = 70
        start_y = box_y + 100
        
        for idx, line in enumerate(lines):
            # Calculate opacity (lines appear one after another)
            line_delay = idx * 0.4  # 0.4 seconds between lines
            line_alpha = max(0, min(255, int(255 * (t - line_delay) * 2)))
            
            if line_alpha > 0:
                # Center text
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = box_x + (box_width - text_width) // 2
                y = start_y + idx * line_height
                
                # Text shadow
                draw.text((x+3, y+3), line, font=quote_font, fill="#00000030")
                # Main text with fade in
                color_with_alpha = BRAND_COLORS["text"] + format(line_alpha, '02x')
                draw.text((x, y), line, font=quote_font, fill=color_with_alpha)
        
        # ===== BLINKING CURSOR =====
        if chars_to_show < total_chars:
            # Show blinking cursor at end of text
            cursor_blink = int(t * 3) % 2 == 0  # Blink 3 times per second
            if cursor_blink and lines:
                last_line = lines[-1]
                bbox = draw.textbbox((0, 0), last_line, font=quote_font)
                cursor_x = box_x + (box_width - bbox[2]) // 2 + bbox[2] + 10
                cursor_y = start_y + (len(lines) - 1) * line_height + 15
                draw.rectangle([cursor_x, cursor_y, cursor_x+3, cursor_y+35], 
                             fill=BRAND_COLORS["accent"])
        
        # ===== AUTHOR REVEAL =====
        if t >= 8:  # Author appears at 8 seconds
            author_alpha = min(255, int(255 * (t - 8) * 2))
            author_text = f"— {author_name}"
            
            bbox = draw.textbbox((0, 0), author_text, font=author_font)
            text_width = bbox[2] - bbox[0]
            author_x = box_x + box_width - text_width - 50
            author_y = box_y + box_height - 80
            
            # Author shadow
            draw.text((author_x+2, author_y+2), author_text, 
                     font=author_font, fill="#00000020")
            # Author with fade in
            author_color = BRAND_COLORS["primary"] + format(author_alpha, '02x')
            draw.text((author_x, author_y), author_text, 
                     font=author_font, fill=author_color)
        
        # ===== ANIMATED DECORATIONS =====
        # Floating circles
        for j in range(4):
            angle = t * 2 + j * 1.5
            circle_x = int(W * 0.2 + j * W * 0.15 + 50 * np.sin(angle))
            circle_y = int(H * 0.3 + 30 * np.cos(angle + j))
            size = 8 + int(4 * np.sin(angle * 1.5))
            
            draw.ellipse([circle_x-size, circle_y-size, 
                         circle_x+size, circle_y+size],
                        outline=BRAND_COLORS["light"] + "80",
                        width=2)
        
        # Progress bar at bottom
        progress_width = int(W * 0.7)
        progress_x = (W - progress_width) // 2
        progress_y = H - 100
        
        # Background
        draw.rounded_rectangle([progress_x, progress_y, 
                               progress_x+progress_width, progress_y+6],
                              radius=3, fill="#00000020")
        
        # Progress fill
        fill_width = int(progress_width * (t / DURATION))
        draw.rounded_rectangle([progress_x, progress_y, 
                               progress_x+fill_width, progress_y+6],
                              radius=3, fill=BRAND_COLORS["accent"])
        
        # Time indicator
        time_text = f"{int(t)}s"
        draw.text((progress_x + fill_width - 20, progress_y - 30), 
                 time_text, font=author_font, fill=BRAND_COLORS["text"])
        
        # Convert to numpy array and add to frames
        frames.append(np.array(img))
    
    # ===== CREATE VIDEO (NO AUDIO) =====
    if len(frames) > 0:
        # Create video clip from frames
        video_clip = mpy.ImageSequenceClip(frames, fps=FPS)
        
        # Write video WITHOUT audio
        output_path = f"{temp_dir}/quote_video_{uuid.uuid4().hex}.mp4"
        video_clip.write_videofile(
            output_path,
            codec='libx264',
            audio=False,  # No audio
            ffmpeg_params=['-preset', 'fast', '-crf', '23', '-pix_fmt', 'yuv420p'],
            logger=None  # Suppress logs
        )
        
        return output_path
    
    return None

# ==================== STREAMLIT UI ====================
def main():
    st.set_page_config(
        page_title="Animated Quote Video Generator",
        page_icon="✨",
        layout="wide"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-title {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 800;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .quote-preview-box {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        border: 2px solid #E5E7EB;
        margin: 1rem 0;
    }
    .stButton button {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
        border: none;
        padding: 0.8rem 2.5rem;
        font-size: 1.1rem;
        border-radius: 50px;
        font-weight: 600;
        transition: all 0.3s;
        width: 100%;
    }
    .stButton button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(79, 70, 229, 0.4);
    }
    .info-box {
        background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%);
        border-radius: 15px;
        padding: 1.5rem;
        border-left: 5px solid #4F46E5;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-title">✨ Animated Quote Video Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Create stunning 10-second quote videos with typewriter animation • No audio • Perfect for social media</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://ik.imagekit.io/ericmwangi/cropped-Parenteen-Kenya-Logo-rec.png", width=200)
        st.markdown("---")
        
        st.subheader("⚙️ Video Settings")
        bg_type = st.selectbox(
            "Background Style",
            ["particles", "gradient", "waves"],
            index=0,
            help="Choose the background animation style"
        )
        
        video_duration = st.slider(
            "Video Duration (seconds)",
            min_value=5,
            max_value=15,
            value=10,
            help="Duration of the generated video"
        )
        
        st.markdown("---")
        st.subheader("🎨 Brand Colors")
        
        # Show color palette
        colors_html = """
        <div style="display: flex; gap: 5px; margin-bottom: 15px;">
            <div style="width: 30px; height: 30px; background-color: #4F46E5; border-radius: 5px;"></div>
            <div style="width: 30px; height: 30px; background-color: #7C3AED; border-radius: 5px;"></div>
            <div style="width: 30px; height: 30px; background-color: #EC4899; border-radius: 5px;"></div>
            <div style="width: 30px; height: 30px; background-color: #8B5CF6; border-radius: 5px;"></div>
        </div>
        """
        st.markdown(colors_html, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("""
        <div class="info-box">
        <h4>💡 Quick Tips</h4>
        <ul style="padding-left: 20px;">
            <li>Keep quotes under 200 characters</li>
            <li>Use clear, impactful language</li>
            <li>Particle background looks best</li>
            <li>Video is generated without audio</li>
            <li>Perfect for Instagram/TikTok</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content - Two columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Quote input section
        st.subheader("✍️ Enter Your Quote")
        
        # Default quote based on your image
        default_quote = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi."""
        
        quote_text = st.text_area(
            "Quote Text",
            value=default_quote,
            height=150,
            placeholder="Enter your inspirational quote here...",
            help="Maximum 300 characters recommended"
        )
        
        col1a, col1b = st.columns(2)
        with col1a:
            author_name = st.text_input(
                "Author Name",
                value="Jane Kariuki",
                placeholder="Author name"
            )
        with col1b:
            author_title = st.text_input(
                "Author Title",
                value="Clinical Psychologist",
                placeholder="Title/credentials"
            )
        
        full_author = f"{author_name}, {author_title}" if author_title else author_name
        
        # Character counter
        char_count = len(quote_text)
        word_count = len(quote_text.split())
        st.caption(f"📊 Characters: {char_count} | Words: {word_count}")
        
        # Warning for long quotes
        if char_count > 300:
            st.warning("⚠️ Quote is quite long. For best results, keep under 300 characters.")
        
        # Generate buttons
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            preview_clicked = st.button(
                "🔍 Preview Quote Design",
                use_container_width=True,
                type="secondary"
            )
        with col_btn2:
            generate_clicked = st.button(
                "🎬 Generate 10-Second Video",
                use_container_width=True,
                type="primary"
            )
        
        # Preview section
        if preview_clicked and quote_text:
            with st.spinner("Creating preview..."):
                preview_img = generate_quote_preview(quote_text, full_author)
                
                st.subheader("📱 Quote Preview")
                st.image(preview_img, use_column_width=True)
                
                # Download preview button
                buf = BytesIO()
                preview_img.save(buf, format="PNG")
                preview_bytes = buf.getvalue()
                
                st.download_button(
                    label="📥 Download Preview Image",
                    data=preview_bytes,
                    file_name=f"quote_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    mime="image/png",
                    use_container_width=True
                )
    
    with col2:
        st.subheader("📊 Video Stats")
        
        if quote_text:
            # Stats cards
            stats_col1, stats_col2 = st.columns(2)
            with stats_col1:
                st.metric("Characters", char_count)
                st.metric("Lines", len(quote_text.split('\n')))
            with stats_col2:
                st.metric("Words", word_count)
                st.metric("Duration", f"{video_duration}s")
            
            # Complexity indicator
            complexity = min(100, char_count * 0.3 + word_count * 1.5)
            st.progress(complexity / 100)
            st.caption(f"Animation complexity: {int(complexity)}%")
            
            # Readability score
            if char_count > 0:
                avg_word_len = char_count / max(word_count, 1)
                if avg_word_len < 5:
                    readability = "Easy"
                    color = "green"
                elif avg_word_len < 7:
                    readability = "Moderate"
                    color = "orange"
                else:
                    readability = "Advanced"
                    color = "red"
                
                st.markdown(f"**Readability:** <span style='color:{color}'>{readability}</span>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("🎯 Best Practices")
        
        st.markdown("""
        ✅ **Short & punchy** (under 15 words)  
        ✅ **Clear message** (one main idea)  
        ✅ **Actionable advice** (inspires action)  
        ✅ **Relatable content** (connects emotionally)  
        ✅ **Brand colors** (consistent identity)  
        
        ⚠️ **Avoid:**  
        • Long paragraphs  
        • Complex jargon  
        • Multiple topics  
        • Passive language
        """)
    
    # Video generation and display
    if generate_clicked and quote_text:
        if char_count > 400:
            st.error("❌ Quote too long! Please keep under 400 characters for optimal video generation.")
        else:
            with st.spinner("🎨 Creating your animated video (this may take 20-30 seconds)..."):
                # Show progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Simulate steps
                steps = ["Initializing", "Creating background", "Animating text", 
                        "Adding effects", "Rendering video", "Finalizing"]
                
                for i, step in enumerate(steps):
                    progress = (i + 1) / len(steps)
                    progress_bar.progress(progress)
                    status_text.text(f"⏳ {step}...")
                    
                    # Small delay for realistic progress
                    import time
                    time.sleep(0.3)
                
                # Generate video (no audio)
                video_path = generate_quote_video_cached(
                    quote_text, 
                    full_author, 
                    bg_type
                )
                
                if video_path:
                    progress_bar.progress(1.0)
                    status_text.text("✅ Video generated successfully!")
                    
                    # Display video
                    st.markdown("---")
                    st.subheader("🎥 Your Generated Video")
                    
                    # Read video file
                    with open(video_path, 'rb') as video_file:
                        video_bytes = video_file.read()
                    
                    # Show video
                    st.video(video_bytes)
                    
                    # Download section
                    st.markdown("---")
                    st.subheader("📥 Download & Share")
                    
                    dl_col1, dl_col2, dl_col3 = st.columns(3)
                    
                    with dl_col1:
                        st.download_button(
                            label="💾 Download MP4",
                            data=video_bytes,
                            file_name=f"quote_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                    
                    with dl_col2:
                        # Generate thumbnail
                        preview_img = generate_quote_preview(quote_text, full_author)
                        buf = BytesIO()
                        preview_img.save(buf, format="PNG")
                        thumbnail_bytes = buf.getvalue()
                        
                        st.download_button(
                            label="🖼️ Download Thumbnail",
                            data=thumbnail_bytes,
                            file_name=f"thumbnail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                            mime="image/png",
                            use_container_width=True
                        )
                    
                    with dl_col3:
                        # Copy share link
                        if st.button("🔗 Copy Share Link", use_container_width=True):
                            st.code("https://parenteenkenya.co.ke/quote-video", language="text")
                    
                    # Video details
                    with st.expander("🔍 Video Details"):
                        st.json({
                            "dimensions": "1080x1920 (9:16 Vertical)",
                            "duration": f"{video_duration} seconds",
                            "frame_rate": "24 FPS",
                            "format": "MP4 H.264",
                            "audio": "None (Silent)",
                            "background": bg_type,
                            "effects": [
                                "Typewriter animation",
                                "Particle system",
                                "Animated borders",
                                "Progress indicator",
                                "Floating elements"
                            ],
                            "brand_colors": list(BRAND_COLORS.values())[:4]
                        })
    
    # Footer
    st.markdown("---")
    footer_cols = st.columns([1, 2, 1])
    with footer_cols[1]:
        st.markdown("""
        <div style="text-align: center; color: #666; padding: 1rem;">
        <p>© 2024 Parenteen Kenya • Quote Video Generator v3.0</p>
        <p style="font-size: 0.9rem;">No audio • Typewriter animation • Brand colors • 10-second format</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
