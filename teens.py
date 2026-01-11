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

# ==================== CACHED GENERATION ====================
@st.cache_data(ttl=3600, show_spinner=False)
def generate_quote_video_cached(quote_text, author_name, bg_style="geometric"):
    """Generate video with caching"""
    return generate_quote_video(quote_text, author_name, bg_style)

# ==================== LOAD LOGO ====================
@st.cache_data
def load_logo():
    """Load and cache logo"""
    try:
        response = requests.get(
            "https://ik.imagekit.io/ericmwangi/cropped-Parenteen-Kenya-Logo-rec.png",
            timeout=10
        )
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except:
        # Create simple placeholder logo
        logo = Image.new('RGBA', (200, 60), (255, 255, 255, 0))
        draw = ImageDraw.Draw(logo)
        draw.rectangle([10, 10, 190, 50], outline="#4F46E5", width=3)
        draw.text((30, 20), "PARENTEEN", fill="#4F46E5", font=ImageFont.load_default())
        draw.text((30, 35), "KENYA", fill="#7C3AED", font=ImageFont.load_default())
        return logo

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

# ==================== GEOMETRIC BACKGROUND GENERATOR ====================
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
        for _ in range(15):
            self.shapes.append({
                'type': 'circle',
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'size': random.randint(30, 150),
                'color': random.choice([
                    BRAND_COLORS["primary"] + "40",
                    BRAND_COLORS["secondary"] + "30",
                    BRAND_COLORS["accent"] + "20"
                ]),
                'speed_x': random.uniform(-0.3, 0.3),
                'speed_y': random.uniform(-0.3, 0.3)
            })
        
        # Generate triangles
        for _ in range(10):
            self.shapes.append({
                'type': 'triangle',
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'size': random.randint(40, 120),
                'color': random.choice([
                    BRAND_COLORS["light"] + "30",
                    BRAND_COLORS["secondary"] + "40",
                    BRAND_COLORS["accent"] + "30"
                ]),
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-1, 1)
            })
        
        # Generate rectangles
        for _ in range(8):
            self.shapes.append({
                'type': 'rectangle',
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'width': random.randint(40, 180),
                'height': random.randint(40, 180),
                'color': random.choice([
                    BRAND_COLORS["primary"] + "20",
                    BRAND_COLORS["dark"] + "30",
                    BRAND_COLORS["light"] + "40"
                ]),
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-0.5, 0.5)
            })
        
        # Generate lines
        for _ in range(12):
            self.shapes.append({
                'type': 'line',
                'x1': random.randint(0, self.width),
                'y1': random.randint(0, self.height),
                'x2': random.randint(0, self.width),
                'y2': random.randint(0, self.height),
                'width': random.randint(2, 8),
                'color': random.choice([
                    BRAND_COLORS["accent"] + "60",
                    BRAND_COLORS["secondary"] + "50",
                    BRAND_COLORS["primary"] + "40"
                ]),
                'speed': random.uniform(-0.2, 0.2)
            })
    
    def update_shapes(self, t):
        """Update shape positions for animation"""
        for shape in self.shapes:
            if shape['type'] == 'circle':
                shape['x'] = (shape['x'] + shape['speed_x']) % self.width
                shape['y'] = (shape['y'] + shape['speed_y']) % self.height
                # Pulsing effect
                shape['size'] = shape.get('original_size', shape['size']) * (1 + 0.1 * math.sin(t * 2))
            
            elif shape['type'] == 'triangle':
                shape['rotation'] = (shape['rotation'] + shape['rotation_speed']) % 360
                # Move in circular pattern
                if 'center_x' not in shape:
                    shape['center_x'] = shape['x']
                    shape['center_y'] = shape['y']
                    shape['orbit_radius'] = random.randint(50, 200)
                    shape['orbit_speed'] = random.uniform(0.5, 1.5)
                
                shape['x'] = shape['center_x'] + shape['orbit_radius'] * math.cos(t * shape['orbit_speed'])
                shape['y'] = shape['center_y'] + shape['orbit_radius'] * math.sin(t * shape['orbit_speed'])
            
            elif shape['type'] == 'rectangle':
                shape['rotation'] = (shape['rotation'] + shape['rotation_speed']) % 360
                # Bounce effect
                if 'bounce_speed' not in shape:
                    shape['bounce_speed'] = random.uniform(0.5, 1.5)
                    shape['bounce_phase'] = random.uniform(0, 2 * math.pi)
                
                bounce_offset = 20 * math.sin(t * shape['bounce_speed'] + shape['bounce_phase'])
                shape['x'] = shape.get('original_x', shape['x']) + bounce_offset
                shape['y'] = shape.get('original_y', shape['y']) + bounce_offset
            
            elif shape['type'] == 'line':
                # Move line endpoints
                move_x = shape['speed'] * math.cos(t * 0.5)
                move_y = shape['speed'] * math.sin(t * 0.5)
                shape['x1'] = (shape['x1'] + move_x) % self.width
                shape['y1'] = (shape['y1'] + move_y) % self.height
                shape['x2'] = (shape['x2'] - move_x) % self.width
                shape['y2'] = (shape['y2'] - move_y) % self.height
    
    def draw(self, draw, t):
        """Draw all shapes"""
        self.update_shapes(t)
        
        for shape in self.shapes:
            color = shape['color']
            alpha = int(color[-2:], 16) if len(color) == 9 else 255
            
            if shape['type'] == 'circle':
                x, y, size = shape['x'], shape['y'], shape['size']
                draw.ellipse([x-size, y-size, x+size, y+size], 
                           fill=color if alpha < 255 else None,
                           outline=color if alpha == 255 else None)
            
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
                
                draw.polygon(points, fill=color if alpha < 255 else None,
                           outline=color if alpha == 255 else None)
            
            elif shape['type'] == 'rectangle':
                x, y = shape['x'], shape['y']
                width, height = shape['width'], shape['height']
                rotation = shape['rotation']
                
                # Create rotated rectangle
                center = (x, y)
                half_w, half_h = width/2, height/2
                
                # Define corners
                corners = [
                    (-half_w, -half_h),
                    (half_w, -half_h),
                    (half_w, half_h),
                    (-half_w, half_h)
                ]
                
                # Rotate corners
                rotated_corners = []
                for cx, cy in corners:
                    rx = cx * math.cos(math.radians(rotation)) - cy * math.sin(math.radians(rotation))
                    ry = cx * math.sin(math.radians(rotation)) + cy * math.cos(math.radians(rotation))
                    rotated_corners.append((center[0] + rx, center[1] + ry))
                
                draw.polygon(rotated_corners, fill=color if alpha < 255 else None,
                           outline=color if alpha == 255 else None)
            
            elif shape['type'] == 'line':
                draw.line([(shape['x1'], shape['y1']), (shape['x2'], shape['y2'])],
                         fill=color, width=shape['width'])

# ==================== TEXT BOX GENERATOR ====================
def calculate_text_box_dimensions(quote_text, author_text, max_width, max_height):
    """Calculate dynamic text box dimensions based on text"""
    # Estimate text dimensions
    char_count = len(quote_text)
    word_count = len(quote_text.split())
    
    # Base dimensions
    base_width = min(800, max(400, char_count * 10))
    base_height = min(600, max(300, word_count * 25))
    
    # Add margins
    margin_x = 100
    margin_y = 80
    
    # Calculate final dimensions
    box_width = min(base_width + margin_x, max_width * 0.85)
    box_height = min(base_height + margin_y, max_height * 0.7)
    
    # Calculate position (centered)
    box_x = (max_width - box_width) // 2
    box_y = (max_height - box_height) // 2
    
    return {
        'x': box_x, 'y': box_y,
        'width': box_width, 'height': box_height,
        'margin_x': 40, 'margin_y': 30
    }

def wrap_text_to_fit(text, font, max_width, draw):
    """Wrap text to fit within max width"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        test_width = bbox[2] - bbox[0]
        
        if test_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

# ==================== VIDEO GENERATION ====================
def generate_quote_video(quote_text, author_name, bg_style="geometric"):
    """Generate 10-second quote video with geometric background"""
    # Video settings
    W, H = 1080, 1920  # Vertical format
    DURATION = 10
    FPS = 24
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Load logo
    logo = load_logo()
    logo = logo.resize((150, 45))  # Resize for video
    
    # Initialize background
    if bg_style == "geometric":
        background = GeometricBackground(W, H)
    elif bg_style == "minimal":
        background = None  # Will use solid color
    
    # Calculate text box dimensions
    box_info = calculate_text_box_dimensions(quote_text, author_name, W, H)
    
    # Generate frames
    frames = []
    
    for i in range(DURATION * FPS):
        # Time progress
        t = i / FPS
        
        # Create base image
        if bg_style == "geometric":
            img = Image.new('RGB', (W, H), color=BRAND_COLORS["bg_dark"])
        else:
            img = Image.new('RGB', (W, H), color=BRAND_COLORS["bg_light"])
        
        draw = ImageDraw.Draw(img)
        
        # ===== ANIMATED BACKGROUND =====
        if bg_style == "geometric":
            # Draw animated geometric shapes
            background.draw(draw, t)
            
            # Add subtle grid overlay
            grid_spacing = 80
            grid_color = BRAND_COLORS["white"] + "10"
            for x in range(0, W, grid_spacing):
                draw.line([(x, 0), (x, H)], fill=grid_color, width=1)
            for y in range(0, H, grid_spacing):
                draw.line([(0, y), (W, y)], fill=grid_color, width=1)
            
            # Add floating dots
            for _ in range(20):
                dot_x = (W * 0.3 + t * 50 + random.random() * W * 0.4) % W
                dot_y = (H * 0.4 + t * 30 + random.random() * H * 0.2) % H
                dot_size = 2 + math.sin(t * 3 + dot_x * 0.01) * 1
                draw.ellipse([dot_x-dot_size, dot_y-dot_size, 
                            dot_x+dot_size, dot_y+dot_size],
                           fill=BRAND_COLORS["accent"] + "80")
        
        else:  # Minimal background
            # Simple gradient
            for y in range(0, H, 2):
                ratio = y / H
                if bg_style == "minimal":
                    r = int(249 * (1 - ratio) + 79 * ratio)
                    g = int(250 * (1 - ratio) + 70 * ratio)
                    b = int(251 * (1 - ratio) + 229 * ratio)
                else:
                    r = int(30 * (1 - ratio) + 79 * ratio)
                    g = int(30 * (1 - ratio) + 70 * ratio)
                    b = int(30 * (1 - ratio) + 229 * ratio)
                draw.line([(0, y), (W, y)], fill=(r, g, b), width=2)
        
        # ===== LOGO =====
        # Position logo at top-left with subtle animation
        logo_x = 40 + 5 * math.sin(t * 1.5)
        logo_y = 40 + 3 * math.cos(t * 2)
        logo_img = logo.copy()
        
        # Add slight rotation to logo
        if bg_style == "geometric":
            logo_img = logo_img.rotate(2 * math.sin(t), expand=True, resample=Image.BICUBIC)
        
        img.paste(logo_img, (int(logo_x), int(logo_y)), logo_img)
        
        # ===== ANIMATED TEXT BOX =====
        # Dynamic box dimensions with breathing effect
        breath = 0.9 + 0.1 * math.sin(t * 3)
        box_x = box_info['x']
        box_y = box_info['y']
        box_width = int(box_info['width'] * breath)
        box_height = int(box_info['height'] * breath)
        
        # Adjust to maintain center
        box_x = (W - box_width) // 2
        box_y = (H - box_height) // 2
        
        # Animated shadow
        shadow_offset = 10 + 5 * math.sin(t * 2)
        shadow_blur = 20
        
        # Draw shadow
        shadow_img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_img)
        shadow_draw.rounded_rectangle(
            [box_x+shadow_offset, box_y+shadow_offset,
             box_x+box_width+shadow_offset, box_y+box_height+shadow_offset],
            radius=40,
            fill="#00000080"
        )
        shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(shadow_blur))
        img = Image.alpha_composite(img.convert('RGBA'), shadow_img)
        draw = ImageDraw.Draw(img)
        
        # Gradient border colors (cycling)
        border_phase = t * 2
        border_colors = [
            BRAND_COLORS["primary"],
            BRAND_COLORS["secondary"],
            BRAND_COLORS["accent"],
            BRAND_COLORS["light"]
        ]
        border_color = border_colors[int(border_phase) % len(border_colors)]
        
        # Draw main box with animated border
        border_width = 6 + 2 * math.sin(t * 4)
        
        # Outer border
        draw.rounded_rectangle(
            [box_x, box_y, box_x+box_width, box_y+box_height],
            radius=40,
            outline=border_color,
            width=int(border_width)
        )
        
        # Inner glow
        draw.rounded_rectangle(
            [box_x+3, box_y+3, box_x+box_width-3, box_y+box_height-3],
            radius=37,
            outline=border_color + "40",
            width=2
        )
        
        # Fill (semi-transparent)
        fill_color = BRAND_COLORS["white"] + "E0" if bg_style == "geometric" else BRAND_COLORS["white"] + "F0"
        draw.rounded_rectangle(
            [box_x+border_width, box_y+border_width,
             box_x+box_width-border_width, box_y+box_height-border_width],
            radius=40-border_width//2,
            fill=fill_color
        )
        
        # Corner decorations
        corner_size = 20
        corner_colors = [BRAND_COLORS["accent"], BRAND_COLORS["secondary"]]
        
        # Top-left
        draw.arc([box_x-5, box_y-5, box_x+corner_size, box_y+corner_size],
                180, 270, fill=corner_colors[0], width=3)
        # Top-right
        draw.arc([box_x+box_width-corner_size, box_y-5, box_x+box_width+5, box_y+corner_size],
                270, 360, fill=corner_colors[1], width=3)
        # Bottom-left
        draw.arc([box_x-5, box_y+box_height-corner_size, box_x+corner_size, box_y+box_height+5],
                90, 180, fill=corner_colors[1], width=3)
        # Bottom-right
        draw.arc([box_x+box_width-corner_size, box_y+box_height-corner_size,
                 box_x+box_width+5, box_y+box_height+5],
                0, 90, fill=corner_colors[0], width=3)
        
        # ===== TYPEWRITER TEXT ANIMATION =====
        try:
            # Load fonts
            title_font = ImageFont.truetype("arial.ttf", 48)
            quote_font = ImageFont.truetype("arial.ttf", 44)
            author_font = ImageFont.truetype("arial.ttf", 36)
        except:
            title_font = ImageFont.load_default()
            quote_font = ImageFont.load_default()
            author_font = ImageFont.load_default()
        
        # Calculate text area
        text_max_width = box_width - 80
        text_max_height = box_height - 100
        
        # Typewriter effect
        total_chars = len(quote_text)
        reveal_time = 7
        chars_to_show = min(int((t / reveal_time) * total_chars), total_chars)
        visible_text = quote_text[:chars_to_show]
        
        # Wrap text to fit
        lines = wrap_text_to_fit(visible_text, quote_font, text_max_width, draw)
        
        # Calculate text positioning
        line_height = 60
        total_text_height = len(lines) * line_height
        text_start_y = box_y + (box_height - total_text_height) // 2
        
        # Draw each line with fade-in effect
        for idx, line in enumerate(lines):
            # Calculate opacity based on line index and time
            line_delay = idx * 0.3
            line_alpha = max(0, min(255, int(255 * (t - line_delay) * 1.5)))
            
            if line_alpha > 0:
                # Center the line
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                line_width = bbox[2] - bbox[0]
                line_x = box_x + (box_width - line_width) // 2
                line_y = text_start_y + idx * line_height
                
                # Text shadow for depth
                shadow_color = "#000000" + format(max(30, line_alpha//3), '02x')
                draw.text((line_x+2, line_y+2), line, font=quote_font, fill=shadow_color)
                
                # Main text with gradient effect
                if line_alpha == 255:
                    # Create gradient text effect
                    for char_idx, char in enumerate(line):
                        char_phase = (t * 2 + char_idx * 0.1) % 1
                        if char_phase < 0.33:
                            char_color = BRAND_COLORS["primary"]
                        elif char_phase < 0.66:
                            char_color = BRAND_COLORS["secondary"]
                        else:
                            char_color = BRAND_COLORS["accent"]
                        
                        # Draw character individually
                        char_bbox = draw.textbbox((0, 0), char, font=quote_font)
                        char_width = char_bbox[2] - char_bbox[0]
                        draw.text((line_x, line_y), char, font=quote_font, fill=char_color)
                        line_x += char_width
                else:
                    # Fading in text
                    text_color = BRAND_COLORS["text"] + format(line_alpha, '02x')
                    draw.text((line_x, line_y), line, font=quote_font, fill=text_color)
        
        # ===== BLINKING CURSOR =====
        if chars_to_show < total_chars and int(t * 3) % 2 == 0:
            if lines:
                last_line = lines[-1]
                bbox = draw.textbbox((0, 0), last_line, font=quote_font)
                cursor_x = box_x + (box_width - bbox[2]) // 2 + bbox[2] + 10
                cursor_y = text_start_y + (len(lines) - 1) * line_height + 15
                
                # Animated cursor
                cursor_height = 30 + 10 * math.sin(t * 8)
                draw.rectangle([cursor_x, cursor_y, cursor_x+4, cursor_y+cursor_height],
                             fill=BRAND_COLORS["accent"])
        
        # ===== AUTHOR REVEAL =====
        if t >= 8:
            author_alpha = min(255, int(255 * (t - 8) * 3))
            author_text = f"— {author_name}"
            
            # Calculate author position
            bbox = draw.textbbox((0, 0), author_text, font=author_font)
            author_width = bbox[2] - bbox[0]
            author_x = box_x + box_width - author_width - 40
            author_y = box_y + box_height - 50
            
            # Animated underline
            underline_width = min(author_width, author_width * (t - 8) * 2)
            draw.line([(author_x, author_y+5), (author_x+underline_width, author_y+5)],
                     fill=BRAND_COLORS["secondary"] + format(author_alpha, '02x'), width=2)
            
            # Author text
            author_color = BRAND_COLORS["primary"] + format(author_alpha, '02x')
            draw.text((author_x, author_y), author_text, font=author_font, fill=author_color)
        
        # ===== ANIMATED DECORATIONS =====
        # Floating quote marks
        if bg_style == "geometric":
            for i in range(2):
                quote_x = box_x - 60 + i * (box_width + 100)
                quote_y = box_y + 50 + 20 * math.sin(t * 2 + i * math.pi)
                draw.text((quote_x, quote_y), "❝", font=title_font,
                         fill=BRAND_COLORS["light"] + "60")
        
        # Progress indicator at bottom
        progress_width = int(W * 0.6)
        progress_x = (W - progress_width) // 2
        progress_y = H - 80
        
        # Background track
        draw.rounded_rectangle([progress_x, progress_y, 
                               progress_x+progress_width, progress_y+8],
                              radius=4, fill="#00000030")
        
        # Animated progress bar
        fill_width = int(progress_width * (t / DURATION))
        
        # Gradient fill
        for i in range(0, fill_width, 5):
            segment_ratio = i / progress_width
            r = int(79 * (1 - segment_ratio) + 236 * segment_ratio)
            g = int(70 * (1 - segment_ratio) + 72 * segment_ratio)
            b = int(229 * (1 - segment_ratio) + 153 * segment_ratio)
            segment_end = min(i + 5, fill_width)
            draw.rectangle([progress_x+i, progress_y, 
                           progress_x+segment_end, progress_y+8],
                          fill=(r, g, b))
        
        # Time indicator with animation
        time_text = f"{int(t)}s"
        time_x = progress_x + fill_width - 20
        time_y = progress_y - 25
        draw.text((time_x, time_y), time_text, font=author_font,
                 fill=BRAND_COLORS["white"])
        
        # Convert to numpy array
        frames.append(np.array(img))
    
    # ===== CREATE VIDEO =====
    if len(frames) > 0:
        # Create video clip
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

# ==================== STREAMLIT UI ====================
def main():
    st.set_page_config(
        page_title="Geometric Quote Video Generator",
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
        letter-spacing: -0.5px;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .card {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 15px 50px rgba(0,0,0,0.1);
        border: 1px solid #E5E7EB;
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
        box-shadow: 0 10px 30px rgba(79, 70, 229, 0.4);
    }
    .color-dot {
        display: inline-block;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        margin-right: 10px;
        vertical-align: middle;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-title">✨ Geometric Quote Video Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Create stunning 10-second quote videos with animated geometric backgrounds • Dynamic text boxes • No audio</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        # Display logo
        logo = load_logo()
        logo = logo.resize((200, 60))
        st.image(logo, use_column_width=True)
        
        st.markdown("---")
        st.subheader("🎨 Design Settings")
        
        bg_style = st.selectbox(
            "Background Style",
            ["geometric", "minimal"],
            index=0,
            help="Choose the background animation style"
        )
        
        st.markdown("---")
        st.subheader("🎯 Brand Colors")
        
        # Color palette display
        colors_display = """
        <div style="margin-bottom: 20px;">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <div class="color-dot" style="background-color: #4F46E5;"></div>
                <span>Primary (Indigo)</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <div class="color-dot" style="background-color: #7C3AED;"></div>
                <span>Secondary (Violet)</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <div class="color-dot" style="background-color: #EC4899;"></div>
                <span>Accent (Pink)</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <div class="color-dot" style="background-color: #8B5CF6;"></div>
                <span>Light Purple</span>
            </div>
        </div>
        """
        st.markdown(colors_display, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%);
                    border-radius: 15px; padding: 1.5rem; border-left: 5px solid #4F46E5;">
        <h4>💡 Features</h4>
        <ul style="padding-left: 20px; margin-bottom: 0;">
            <li>Animated geometric shapes</li>
            <li>Dynamic text box sizing</li>
            <li>Typewriter animation</li>
            <li>Logo integration</li>
            <li>10-second videos</li>
            <li>No audio (silent)</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("✍️ Enter Your Quote")
        
        # Example quote from your image
        default_quote = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi."""
        
        quote_text = st.text_area(
            "Quote Text",
            value=default_quote,
            height=120,
            placeholder="Enter your inspirational quote here...",
            help="The text box will automatically adjust to fit your text"
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
                placeholder="Title or credentials"
            )
        
        full_author = f"{author_name}, {author_title}" if author_title else author_name
        
        # Stats
        char_count = len(quote_text)
        word_count = len(quote_text.split())
        
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        with col_stats1:
            st.metric("Characters", char_count)
        with col_stats2:
            st.metric("Words", word_count)
        with col_stats3:
            lines = len(quote_text.split('\n'))
            st.metric("Lines", lines)
        
        # Warning for long quotes
        if char_count > 500:
            st.warning("⚠️ Very long quote! Consider shortening for best visual results.")
        elif char_count > 300:
            st.info("ℹ️ Long quote - text box will expand to fit content.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Generate button
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            generate_clicked = st.button(
                "🎬 Generate Geometric Video",
                use_container_width=True,
                type="primary",
                help="Create 10-second animated video with geometric background"
            )
        
        with col_btn2:
            if st.button(
                "🔍 Preview First Frame",
                use_container_width=True,
                type="secondary"
            ):
                st.session_state.preview_frame = True
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 Design Preview")
        
        # Show dynamic box size calculation
        if quote_text:
            W, H = 1080, 1920
            box_info = calculate_text_box_dimensions(quote_text, full_author, W, H)
            
            # Visual representation
            box_ratio = box_info['width'] / W
            if box_ratio < 0.5:
                box_size = "Small"
                color = "green"
            elif box_ratio < 0.7:
                box_size = "Medium"
                color = "orange"
            else:
                box_size = "Large"
                color = "red"
            
            st.markdown(f"**Text Box Size:** <span style='color:{color}'>{box_size}</span>", unsafe_allow_html=True)
            st.progress(min(1.0, box_ratio / 0.85))
            
            # Box dimensions
            st.markdown(f"""
            **Dimensions:** {box_info['width']} × {box_info['height']}px  
            **Position:** ({box_info['x']}, {box_info['y']})  
            **Margins:** {box_info['margin_x']}px horizontal, {box_info['margin_y']}px vertical
            """)
            
            # Text fitting
            avg_chars_per_line = char_count / max(lines, 1)
            if avg_chars_per_line < 40:
                fit = "Good"
                fit_color = "green"
            elif avg_chars_per_line < 60:
                fit = "OK"
                fit_color = "orange"
            else:
                fit = "Tight"
                fit_color = "red"
            
            st.markdown(f"**Text Fit:** <span style='color:{fit_color}'>{fit}</span>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("⚙️ Animation Effects")
        
        effects = [
            "✅ Geometric shapes animation",
            "✅ Text box breathing effect",
            "✅ Gradient border colors",
            "✅ Typewriter text reveal",
            "✅ Blinking cursor",
            "✅ Floating decorations",
            "✅ Progress indicator",
            "✅ Logo animation"
        ]
        
        for effect in effects:
            st.markdown(f"• {effect}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Generate video
    if generate_clicked and quote_text:
        if char_count > 800:
            st.error("❌ Quote too long! Maximum 800 characters.")
        else:
            with st.spinner("🎨 Creating geometric video (20-30 seconds)..."):
                # Show progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                steps = [
                    "Generating geometric shapes...",
                    "Animating background...",
                    "Creating text box...",
                    "Applying typewriter effect...",
                    "Adding decorations...",
                    "Rendering video frames...",
                    "Finalizing output..."
                ]
                
                for i, step in enumerate(steps):
                    progress = (i + 1) / len(steps)
                    progress_bar.progress(progress)
                    status_text.text(f"⏳ {step}")
                    
                    import time
                    time.sleep(0.3)
                
                # Generate video
                video_path = generate_quote_video_cached(
                    quote_text,
                    full_author,
                    bg_style
                )
                
                if video_path:
                    progress_bar.progress(1.0)
                    status_text.text("✅ Video created successfully!")
                    
                    # Display video
                    st.markdown("---")
                    st.subheader("🎥 Your Geometric Quote Video")
                    
                    with open(video_path, 'rb') as f:
                        video_bytes = f.read()
                    
                    st.video(video_bytes)
                    
                    # Download section
                    st.markdown("---")
                    st.subheader("📥 Download")
                    
                    dl_col1, dl_col2 = st.columns(2)
                    
                    with dl_col1:
                        st.download_button(
                            label="💾 Download MP4",
                            data=video_bytes,
                            file_name=f"geometric_quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                    
                    with dl_col2:
                        # Show first frame as thumbnail
                        if 'preview_img' not in locals():
                            # Generate first frame
                            img = Image.new('RGB', (1080, 1920), color=BRAND_COLORS["bg_dark"])
                            buf = BytesIO()
                            img.save(buf, format="PNG")
                            preview_bytes = buf.getvalue()
                        
                        st.download_button(
                            label="🖼️ Save Thumbnail",
                            data=preview_bytes,
                            file_name="video_thumbnail.png",
                            mime="image/png",
                            use_container_width=True
                        )
                    
                    # Technical details
                    with st.expander("🔧 Technical Details"):
                        st.json({
                            "resolution": "1080×1920 (9:16)",
                            "duration": "10 seconds",
                            "frame_rate": "24 FPS",
                            "format": "MP4 H.264",
                            "background": bg_style,
                            "logo_included": True,
                            "dynamic_text_box": True,
                            "animations": [
                                "Geometric shapes",
                                "Text box breathing",
                                "Border color cycling",
                                "Typewriter effect",
                                "Cursor blink",
                                "Floating elements",
                                "Progress bar"
                            ]
                        })
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p style="font-size: 0.9rem;">
            <strong>Geometric Quote Video Generator v4.0</strong><br>
            Animated geometric backgrounds • Dynamic text boxes • Brand colors • 10-second format
        </p>
        <p style="font-size: 0.8rem; color: #999;">
            Inspired by geometric design patterns • Optimized for social media • No audio
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()