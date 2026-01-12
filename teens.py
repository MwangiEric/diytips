import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import moviepy.editor as mpy
from moviepy.editor import *
from io import BytesIO
import tempfile
import uuid
import random
import math
from datetime import datetime
import requests

# ==================== GLOBAL CACHE ====================
LOGO_CACHE = None
FONT_CACHE = {}

# ==================== CACHED RESOURCES ====================
@st.cache_data
def load_logo_once():
    """Load logo once and cache"""
    try:
        response = requests.get(
            "https://ik.imagekit.io/ericmwangi/cropped-Parenteen-Kenya-Logo-rec.png",
            timeout=10
        )
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except:
        # Create placeholder
        logo = Image.new('RGBA', (250, 80), (255, 255, 255, 0))
        draw = ImageDraw.Draw(logo)
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except:
            font = ImageFont.load_default()
        draw.text((20, 20), "PARENTEEN", fill="#4F46E5", font=font)
        draw.text((20, 50), "KENYA", fill="#7C3AED", font=font)
        return logo

@st.cache_data
def load_font_once(size=48):
    """Load font with fallback to Arial"""
    try:
        # Try multiple font paths
        font_paths = [
            "arial.ttf",
            "Arial.ttf",
            "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
            "/System/Library/Fonts/Arial.ttf",
            "C:/Windows/Fonts/arial.ttf"
        ]
        
        for path in font_paths:
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
        
        # If no font found, try to download a font
        try:
            # Try to use a free Google Font via URL
            response = requests.get("https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf", timeout=5)
            font_file = BytesIO(response.content)
            return ImageFont.truetype(font_file, size)
        except:
            # Last resort: create a bitmap font
            return ImageFont.load_default()
            
    except:
        return ImageFont.load_default()

# ==================== BRAND COLORS ====================
BRAND_COLORS = {
    "primary": "#4F46E5",     # Indigo
    "secondary": "#7C3AED",   # Violet
    "accent": "#EC4899",      # Pink
    "light": "#8B5CF6",       # Light purple
    "dark": "#3730A3",        # Dark blue
    "text": "#1F2937",        # Gray-800
    "bg_light": "#F9FAFB",    # Light gray
    "bg_dark": "#1E1B4B",     # Dark indigo
    "white": "#FFFFFF",
    "black": "#000000"
}

# ==================== GEOMETRIC BACKGROUND ====================
class GeometricBackground:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.shapes = []
        self.generate_shapes()
    
    def generate_shapes(self):
        """Generate random geometric shapes"""
        self.shapes = []
        
        # Generate circles
        for _ in range(12):
            self.shapes.append({
                'type': 'circle',
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'size': random.randint(40, 120),
                'color': random.choice([
                    BRAND_COLORS["primary"] + "30",
                    BRAND_COLORS["secondary"] + "40",
                    BRAND_COLORS["accent"] + "20"
                ]),
                'speed_x': random.uniform(-0.5, 0.5),
                'speed_y': random.uniform(-0.5, 0.5)
            })
        
        # Generate triangles
        for _ in range(8):
            self.shapes.append({
                'type': 'triangle',
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'size': random.randint(50, 100),
                'color': random.choice([
                    BRAND_COLORS["light"] + "40",
                    BRAND_COLORS["secondary"] + "30"
                ]),
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-1, 1)
            })
    
    def update_shapes(self, t):
        """Update shape positions"""
        for shape in self.shapes:
            if shape['type'] == 'circle':
                shape['x'] = (shape['x'] + shape['speed_x']) % self.width
                shape['y'] = (shape['y'] + shape['speed_y']) % self.height
                # Pulsing effect
                shape['size'] = shape.get('original_size', shape['size']) * (1 + 0.1 * math.sin(t * 2))
            
            elif shape['type'] == 'triangle':
                shape['rotation'] = (shape['rotation'] + shape['rotation_speed']) % 360
    
    def draw(self, draw, t):
        """Draw all shapes"""
        self.update_shapes(t)
        
        for shape in self.shapes:
            color = shape['color']
            
            if shape['type'] == 'circle':
                x, y, size = shape['x'], shape['y'], shape['size']
                draw.ellipse([x-size, y-size, x+size, y+size], 
                           fill=color if len(color) == 9 else None,
                           outline=color if len(color) == 7 else None)
            
            elif shape['type'] == 'triangle':
                x, y, size = shape['x'], shape['y'], shape['size']
                rotation = shape['rotation']
                
                # Calculate triangle points
                points = []
                for i in range(3):
                    angle = rotation + i * 120
                    px = x + size * math.cos(math.radians(angle))
                    py = y + size * math.sin(math.radians(angle))
                    points.append((px, py))
                
                draw.polygon(points, fill=color if len(color) == 9 else None,
                           outline=color if len(color) == 7 else None)

# ==================== TEXT UTILITIES ====================
def wrap_text_to_fit(text, font, max_width):
    """Wrap text to fit within max width"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        # Create test string to check width
        test_line = ' '.join(current_line + [word]) if current_line else word
        
        # Use textbbox for accurate measurement
        left, top, right, bottom = font.getbbox(test_line)
        test_width = right - left
        
        if test_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def calculate_text_box(text, font, max_width, max_height, padding=80):
    """Calculate text box dimensions"""
    lines = wrap_text_to_fit(text, font, max_width - padding)
    
    # Calculate line heights
    line_height = font.getbbox("A")[3] - font.getbbox("A")[1] + 10
    total_height = len(lines) * line_height
    
    # Calculate box dimensions
    box_width = max_width
    box_height = total_height + padding
    
    # Ensure minimum size
    box_width = max(400, box_width)
    box_height = max(300, box_height)
    
    return {
        'lines': lines,
        'line_height': line_height,
        'box_width': box_width,
        'box_height': box_height,
        'total_height': total_height
    }

# ==================== VIDEO GENERATION ====================
@st.cache_data(ttl=3600, show_spinner=False)
def generate_quote_video_cached(quote_text, author_name, bg_style="geometric"):
    """Generate video with caching"""
    return generate_quote_video(quote_text, author_name, bg_style)

def generate_quote_video(quote_text, author_name, bg_style="geometric"):
    """Generate 10-second quote video"""
    # Video settings
    W, H = 1080, 1920  # Vertical format
    DURATION = 10
    FPS = 24
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Load resources
    logo = load_logo_once()
    logo = logo.resize((200, 64))
    
    # Load fonts with different sizes
    font_large = load_font_once(48)  # For title/headings
    font_quote = load_font_once(42)  # For quote text
    font_author = load_font_once(36)  # For author
    
    # Initialize background
    if bg_style == "geometric":
        background = GeometricBackground(W, H)
    
    # Pre-calculate text box
    max_text_width = int(W * 0.7)  # 70% of width for text
    text_info = calculate_text_box(quote_text, font_quote, max_text_width, H)
    
    # Calculate fixed box position (centered)
    box_width = int(W * 0.8)
    box_height = text_info['box_height'] + 120  # Add space for author
    box_x = (W - box_width) // 2
    box_y = (H - box_height) // 2
    
    # Store frames
    frames = []
    
    # Generate each frame
    for frame_idx in range(DURATION * FPS):
        t = frame_idx / FPS  # Time in seconds
        
        # Create base image
        if bg_style == "geometric":
            img = Image.new('RGB', (W, H), color=BRAND_COLORS["bg_dark"])
        else:
            img = Image.new('RGB', (W, H), color=BRAND_COLORS["bg_light"])
        
        draw = ImageDraw.Draw(img)
        
        # ===== BACKGROUND =====
        if bg_style == "geometric":
            # Draw animated geometric shapes
            background.draw(draw, t)
            
            # Add subtle gradient overlay
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            for y in range(0, H, 10):
                alpha = int(20 * (1 - abs(y - H/2) / (H/2)))
                overlay_draw.line([(0, y), (W, y)], 
                                 fill=BRAND_COLORS["dark"] + format(alpha, '02x'), 
                                 width=10)
            img = Image.alpha_composite(img.convert('RGBA'), overlay)
            draw = ImageDraw.Draw(img)
        
        # ===== LOGO (TOP MIDDLE) =====
        logo_x = (W - logo.width) // 2
        logo_y = 60
        
        # Add subtle animation to logo
        logo_offset = 3 * math.sin(t * 2)
        img.paste(logo, (int(logo_x), int(logo_y + logo_offset)), logo)
        
        # ===== QUOTE BOX =====
        # Animated shadow
        shadow_offset = 8 + 4 * math.sin(t * 3)
        shadow_color = "#00000060"
        
        # Draw shadow
        draw.rounded_rectangle(
            [box_x + shadow_offset, box_y + shadow_offset,
             box_x + box_width + shadow_offset, box_y + box_height + shadow_offset],
            radius=25,
            fill=shadow_color
        )
        
        # ANIMATED BORDERS
        border_phase = t * 2  # Border animation speed
        
        # Calculate border colors (cycling through brand colors)
        border_colors = [
            BRAND_COLORS["primary"],
            BRAND_COLORS["secondary"],
            BRAND_COLORS["accent"],
            BRAND_COLORS["light"]
        ]
        border_color_idx = int(border_phase) % len(border_colors)
        border_color = border_colors[border_color_idx]
        
        # Animated border width
        border_width = 5 + 2 * math.sin(t * 4)
        
        # Draw main box with animated border
        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_width, box_y + box_height],
            radius=25,
            fill=BRAND_COLORS["white"] + "F0",  # Semi-transparent white
            outline=border_color,
            width=int(border_width)
        )
        
        # Inner glow effect
        glow_width = 2
        draw.rounded_rectangle(
            [box_x + glow_width, box_y + glow_width,
             box_x + box_width - glow_width, box_y + box_height - glow_width],
            radius=25 - glow_width,
            outline=border_color + "40",
            width=glow_width
        )
        
        # Corner accents (animated)
        corner_size = 15
        for i, corner in enumerate([(box_x, box_y), (box_x + box_width, box_y),
                                   (box_x, box_y + box_height), (box_x + box_width, box_y + box_height)]):
            cx, cy = corner
            
            # Different colors for each corner
            corner_color = [
                BRAND_COLORS["accent"],
                BRAND_COLORS["secondary"],
                BRAND_COLORS["primary"],
                BRAND_COLORS["light"]
            ][i]
            
            # Animated corner rotation
            rotation = t * 30 + i * 90
            
            # Draw corner triangle
            points = []
            for j in range(3):
                angle = rotation + j * 120
                px = cx + corner_size * math.cos(math.radians(angle))
                py = cy + corner_size * math.sin(math.radians(angle))
                points.append((px, py))
            
            draw.polygon(points, fill=corner_color + "80")
        
        # ===== QUOTE TEXT =====
        text_x = box_x + 40
        text_y = box_y + 60
        
        # Typewriter effect
        total_chars = len(quote_text)
        reveal_time = 7  # 7 seconds to reveal all text
        chars_to_show = min(int((t / reveal_time) * total_chars), total_chars)
        visible_text = quote_text[:chars_to_show]
        
        # Get wrapped lines for visible text
        visible_info = calculate_text_box(visible_text, font_quote, max_text_width, H)
        visible_lines = visible_info['lines']
        
        # Draw visible lines with fade-in effect
        line_spacing = 55
        for line_idx, line in enumerate(visible_lines):
            # Calculate opacity based on line appearance time
            line_delay = line_idx * 0.2
            line_alpha = max(0, min(255, int(255 * (t - line_delay) * 2)))
            
            if line_alpha > 0:
                # Center the line horizontally
                left, top, right, bottom = font_quote.getbbox(line)
                line_width = right - left
                centered_x = box_x + (box_width - line_width) // 2
                
                # Text shadow for readability
                shadow_alpha = min(100, line_alpha // 3)
                draw.text((centered_x + 2, text_y + line_idx * line_spacing + 2),
                         line, font=font_quote,
                         fill="#000000" + format(shadow_alpha, '02x'))
                
                # Main text with opacity
                text_color = BRAND_COLORS["text"] + format(line_alpha, '02x')
                draw.text((centered_x, text_y + line_idx * line_spacing),
                         line, font=font_quote, fill=text_color)
        
        # ===== BLINKING CURSOR =====
        if chars_to_show < total_chars and int(t * 3) % 2 == 0:
            if visible_lines:
                last_line = visible_lines[-1]
                left, top, right, bottom = font_quote.getbbox(last_line)
                cursor_x = box_x + (box_width - right) // 2 + right + 15
                cursor_y = text_y + (len(visible_lines) - 1) * line_spacing + 10
                
                # Animated cursor height
                cursor_height = 35 + 10 * math.sin(t * 8)
                draw.rectangle([cursor_x, cursor_y, cursor_x + 3, cursor_y + cursor_height],
                             fill=BRAND_COLORS["accent"])
        
        # ===== AUTHOR =====
        if t >= 8:
            author_alpha = min(255, int(255 * (t - 8) * 3))
            author_text = f"— {author_name}"
            
            # Calculate author position (right-aligned in box)
            left, top, right, bottom = font_author.getbbox(author_text)
            author_width = right - left
            author_x = box_x + box_width - author_width - 40
            author_y = box_y + box_height - 60
            
            # Animated underline
            underline_width = min(author_width, author_width * (t - 8) * 2)
            draw.line([(author_x, author_y + 5),
                      (author_x + underline_width, author_y + 5)],
                     fill=BRAND_COLORS["secondary"] + format(author_alpha, '02x'),
                     width=2)
            
            # Author text
            author_color = BRAND_COLORS["primary"] + format(author_alpha, '02x')
            draw.text((author_x, author_y), author_text, font=font_author, fill=author_color)
        
        # ===== TIME INDICATOR =====
        # Progress bar at bottom
        progress_width = int(W * 0.6)
        progress_x = (W - progress_width) // 2
        progress_y = H - 100
        
        # Background track
        draw.rounded_rectangle([progress_x, progress_y,
                               progress_x + progress_width, progress_y + 6],
                              radius=3, fill="#00000030")
        
        # Animated progress fill
        fill_width = int(progress_width * (t / DURATION))
        for i in range(0, fill_width, 10):
            segment_end = min(i + 10, fill_width)
            color_ratio = i / progress_width
            
            # Gradient color
            r = int(79 * (1 - color_ratio) + 236 * color_ratio)
            g = int(70 * (1 - color_ratio) + 72 * color_ratio)
            b = int(229 * (1 - color_ratio) + 153 * color_ratio)
            
            draw.rectangle([progress_x + i, progress_y,
                           progress_x + segment_end, progress_y + 6],
                          fill=(r, g, b))
        
        # Time text
        time_text = f"{int(t)}s"
        left, top, right, bottom = font_author.getbbox(time_text)
        time_width = right - left
        time_x = progress_x + fill_width - time_width // 2
        time_y = progress_y - 30
        
        draw.text((time_x, time_y), time_text, font=font_author,
                 fill=BRAND_COLORS["white"])
        
        # ===== ADD FRAME =====
        frames.append(np.array(img))
    
    # ===== CREATE VIDEO =====
    if frames:
        # Create video from frames
        video_clip = mpy.ImageSequenceClip(frames, fps=FPS)
        
        # Write video file
        output_path = f"{temp_dir}/quote_video_{uuid.uuid4().hex}.mp4"
        video_clip.write_videofile(
            output_path,
            codec='libx264',
            audio=False,
            ffmpeg_params=['-preset', 'fast', '-crf', '23', '-pix_fmt', 'yuv420p'],
            logger=None
        )
        
        return output_path
    
    return None

# ==================== PREVIEW GENERATOR ====================
def generate_preview_image(quote_text, author_name):
    """Generate preview image of the quote"""
    W, H = 800, 1200
    
    # Create image
    img = Image.new('RGB', (W, H), color=BRAND_COLORS["bg_dark"])
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    font_quote = load_font_once(42)
    font_author = load_font_once(36)
    
    # Add simple gradient
    for y in range(0, H, 5):
        ratio = y / H
        r = int(30 * (1 - ratio) + 79 * ratio)
        g = int(30 * (1 - ratio) + 70 * ratio)
        b = int(30 * (1 - ratio) + 229 * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b), width=5)
    
    # Text box
    box_width = int(W * 0.8)
    box_height = int(H * 0.6)
    box_x = (W - box_width) // 2
    box_y = (H - box_height) // 2
    
    # Box with shadow
    draw.rounded_rectangle(
        [box_x + 8, box_y + 8, box_x + box_width + 8, box_y + box_height + 8],
        radius=25, fill="#00000040"
    )
    
    # Main box
    draw.rounded_rectangle(
        [box_x, box_y, box_x + box_width, box_y + box_height],
        radius=25, fill=BRAND_COLORS["white"], outline=BRAND_COLORS["primary"], width=4
    )
    
    # Wrap text
    max_text_width = box_width - 80
    text_info = calculate_text_box(quote_text, font_quote, max_text_width, box_height)
    lines = text_info['lines']
    
    # Draw text
    text_y = box_y + 60
    line_spacing = 55
    
    for i, line in enumerate(lines):
        left, top, right, bottom = font_quote.getbbox(line)
        line_width = right - left
        centered_x = box_x + (box_width - line_width) // 2
        
        # Shadow
        draw.text((centered_x + 2, text_y + i * line_spacing + 2),
                 line, font=font_quote, fill="#00000030")
        
        # Main text
        draw.text((centered_x, text_y + i * line_spacing),
                 line, font=font_quote, fill=BRAND_COLORS["text"])
    
    # Add author
    author_text = f"— {author_name}"
    left, top, right, bottom = font_author.getbbox(author_text)
    author_x = box_x + box_width - (right - left) - 40
    author_y = box_y + box_height - 60
    
    draw.text((author_x, author_y), author_text, font=font_author,
             fill=BRAND_COLORS["primary"])
    
    return img

# ==================== STREAMLIT APP ====================
def main():
    st.set_page_config(
        page_title="Enhanced Quote Video Generator",
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
        font-size: 3rem;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    .card {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        border: 1px solid #E5E7EB;
        margin-bottom: 2rem;
    }
    .stButton button {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        font-size: 1.1rem;
        border-radius: 50px;
        font-weight: 600;
        transition: all 0.3s;
        width: 100%;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(79, 70, 229, 0.4);
    }
    .text-sample {
        font-size: 1.2rem;
        line-height: 1.6;
        padding: 1.5rem;
        background: #F9FAFB;
        border-radius: 10px;
        border-left: 4px solid #4F46E5;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-title">✨ Enhanced Quote Video Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666; font-size: 1.1rem;">10-second videos • Large readable text • Animated borders • Top logo</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        # Show logo
        logo = load_logo_once()
        logo = logo.resize((180, 58))
        st.image(logo, use_column_width=True)
        
        st.markdown("---")
        st.subheader("⚙️ Settings")
        
        bg_style = st.selectbox(
            "Background Style",
            ["geometric", "minimal"],
            index=0
        )
        
        st.markdown("---")
        st.subheader("📏 Text Sizes")
        
        # Font size preview
        st.markdown("""
        **Font Sizes Used:**
        - Quote text: 42px
        - Author: 36px
        - Titles: 48px
        
        *Auto-wrapped for readability*
        """)
        
        st.markdown("---")
        st.markdown("""
        <div style="background: #F3F4F6; padding: 1rem; border-radius: 10px;">
        <h4>🎯 Key Features</h4>
        <ul style="margin-bottom: 0;">
            <li>Large readable text</li>
            <li>Logo top center</li>
            <li>Animated borders</li>
            <li>Typewriter effect</li>
            <li>10-second duration</li>
            <li>Frame-by-frame rendering</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("✍️ Enter Quote")
        
        # Default quote
        default_quote = """Mental health is not a destination, but a process. It's about how you drive, not where you're going. Take care of your mind as you would your body."""
        
        quote_text = st.text_area(
            "Quote Text",
            value=default_quote,
            height=120,
            placeholder="Enter your inspirational quote here..."
        )
        
        col1a, col1b = st.columns(2)
        with col1a:
            author_name = st.text_input(
                "Author Name",
                value="Jane Kariuki"
            )
        with col1b:
            author_title = st.text_input(
                "Title",
                value="Clinical Psychologist"
            )
        
        full_author = f"{author_name}, {author_title}" if author_title else author_name
        
        # Text stats
        char_count = len(quote_text)
        word_count = len(quote_text.split())
        
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        with col_stats1:
            st.metric("Characters", char_count)
        with col_stats2:
            st.metric("Words", word_count)
        with col_stats3:
            st.metric("Estimated Lines", len(quote_text) // 40 + 1)
        
        # Text sample preview
        st.markdown("---")
        st.subheader("📱 Text Preview")
        
        if quote_text:
            # Show how text will look
            st.markdown('<div class="text-sample">', unsafe_allow_html=True)
            st.write(quote_text[:200] + "..." if len(quote_text) > 200 else quote_text)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.caption(f"*Author: {full_author}*")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Generate buttons
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            generate_clicked = st.button(
                "🎬 Generate 10-Second Video",
                use_container_width=True,
                type="primary"
            )
        
        with col_btn2:
            preview_clicked = st.button(
                "🔍 Preview Design",
                use_container_width=True
            )
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("⚡ Quick Tips")
        
        tips = """
        1. **Keep it concise** - 2-3 sentences work best
        2. **Use clear language** - Avoid complex jargon
        3. **Include author** - Adds credibility
        4. **Check length** - Under 300 chars for best results
        5. **Be inspiring** - Positive, actionable messages
        """
        
        st.markdown(tips)
        
        st.markdown("---")
        st.subheader("🎨 Design Elements")
        
        elements = """
        ✅ **Large Text** - Easy to read
        ✅ **Centered Logo** - Top middle position
        ✅ **Animated Borders** - Color-changing edges
        ✅ **Fixed Rectangle** - Consistent size
        ✅ **Typewriter Effect** - Text appears gradually
        ✅ **Author Fade-in** - Appears at 8 seconds
        ✅ **Time Indicator** - Shows progress
        ✅ **Geometric BG** - Animated shapes (optional)
        """
        
        st.markdown(elements)
        
        st.markdown("---")
        st.subheader("⏱️ Video Specs")
        
        st.markdown("""
        - **Duration:** 10 seconds
        - **Resolution:** 1080×1920 (9:16)
        - **FPS:** 24 frames/second
        - **Format:** MP4 (H.264)
        - **Audio:** None (silent)
        - **Rendering:** Frame-by-frame
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Preview design
    if preview_clicked and quote_text:
        with st.spinner("Creating preview..."):
            preview_img = generate_preview_image(quote_text, full_author)
            
            st.markdown("---")
            st.subheader("🖼️ Design Preview")
            
            col_preview1, col_preview2 = st.columns([3, 1])
            with col_preview1:
                st.image(preview_img, use_column_width=True)
            
            with col_preview2:
                # Download preview
                buf = BytesIO()
                preview_img.save(buf, format="PNG")
                preview_bytes = buf.getvalue()
                
                st.download_button(
                    label="📥 Download Preview",
                    data=preview_bytes,
                    file_name=f"quote_preview_{datetime.now().strftime('%Y%m%d')}.png",
                    mime="image/png",
                    use_container_width=True
                )
                
                st.markdown("""
                **Preview Shows:**
                - Text size & layout
                - Color scheme
                - Box positioning
                - Font readability
                """)
    
    # Generate video
    if generate_clicked and quote_text:
        if char_count > 500:
            st.error("Quote is too long! Please keep under 500 characters.")
        else:
            with st.spinner("🎨 Generating video (15-20 seconds)..."):
                # Show progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                steps = [
                    "Loading resources...",
                    "Calculating layout...",
                    "Generating frames...",
                    "Animating elements...",
                    "Rendering video...",
                    "Finalizing..."
                ]
                
                for i, step in enumerate(steps):
                    progress = (i + 1) / len(steps)
                    progress_bar.progress(progress)
                    status_text.text(f"⏳ {step}")
                    
                    import time
                    time.sleep(0.4)
                
                # Generate video
                video_path = generate_quote_video_cached(
                    quote_text,
                    full_author,
                    bg_style
                )
                
                if video_path:
                    progress_bar.progress(1.0)
                    status_text.text("✅ Video ready!")
                    
                    # Display video
                    st.markdown("---")
                    st.subheader("🎥 Your Video")
                    
                    with open(video_path, 'rb') as f:
                        video_bytes = f.read()
                    
                    st.video(video_bytes)
                    
                    # Download section
                    st.markdown("---")
                    st.subheader("📥 Download Video")
                    
                    col_dl1, col_dl2 = st.columns(2)
                    
                    with col_dl1:
                        st.download_button(
                            label="💾 Download MP4",
                            data=video_bytes,
                            file_name=f"quote_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                    
                    with col_dl2:
                        # Share options
                        if st.button("🔗 Copy Share Link", use_container_width=True):
                            st.code("https://parenteenkenya.co.ke/quote-video", language="bash")
                    
                    # Technical details
                    with st.expander("🔧 Technical Details"):
                        st.json({
                            "video": {
                                "duration": "10 seconds",
                                "frames": DURATION * FPS,
                                "resolution": "1080x1920",
                                "aspect_ratio": "9:16",
                                "format": "MP4 H.264"
                            },
                            "text": {
                                "font_size": "42px",
                                "font_family": "Arial (with fallbacks)",
                                "box_size": "Fixed rectangle",
                                "alignment": "Center",
                                "animation": "Typewriter effect"
                            },
                            "design": {
                                "logo_position": "Top center",
                                "border_animation": "Color cycling + pulsing",
                                "background": bg_style,
                                "author_display": "Fade-in at 8s"
                            }
                        })
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem 0;">
        <p><strong>Enhanced Quote Video Generator v5.0</strong></p>
        <p style="font-size: 0.9rem;">Large readable text • Animated borders • 10-second videos • Frame-by-frame rendering</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()