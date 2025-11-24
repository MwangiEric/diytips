# app.py (SIMPLIFIED AI LAYOUT ANIMATOR)
import streamlit as st
import numpy as np
import imageio
import tempfile
import base64
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io
import requests

# Set page config
st.set_page_config(page_title="AI Layout Animator", layout="centered")

# Simple styling
st.markdown("""
<style>
.main { background: #0f0c29; }
.glass { background: rgba(255,255,255,0.1); border-radius: 16px; padding: 2rem; margin: 2rem auto; max-width: 800px; }
.video-container { margin: 2rem 0; border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ------------- Simple Layout Engine -------------
class SimpleLayoutEngine:
    def analyze_layout(self, text, logo_size, screen_width, screen_height):
        """Simple rule-based layout analysis"""
        text_length = len(text)
        
        if text_length < 50:
            return {
                "logo_position": "top_center",
                "font_size": min(100, screen_height // 10),
                "text_start_y": 200,
                "line_spacing": 1.4
            }
        else:
            return {
                "logo_position": "top_left", 
                "font_size": min(70, screen_height // 12),
                "text_start_y": 150,
                "line_spacing": 1.6
            }

# ------------- Logo Handler -------------
def load_logo():
    """Load logo with fallback"""
    try:
        logo_url = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
        response = requests.get(logo_url)
        logo_image = Image.open(io.BytesIO(response.content))
        if logo_image.mode != 'RGBA':
            logo_image = logo_image.convert('RGBA')
        return logo_image.resize((120, 60), Image.Resampling.LANCZOS)
    except:
        # Create simple fallback logo
        img = Image.new('RGBA', (120, 60), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([5, 15, 115, 45], fill=(255, 215, 0, 180))
        draw.text((15, 20), "BRAND", fill=(0, 0, 0, 255))
        return img

# ------------- Frame Generator -------------
class FrameGenerator:
    def __init__(self):
        self.layout_engine = SimpleLayoutEngine()
        self.logo = load_logo()
    
    def create_frame(self, text, progress, frame_idx, total_frames, width, height, text_color="#FFD700"):
        """Create animated frame"""
        # Generate background
        bg = self.generate_background(width, height, frame_idx, total_frames)
        img = Image.fromarray(bg)
        draw = ImageDraw.Draw(img)
        
        # Add logo
        if self.logo:
            img = self.add_logo(img, self.logo)
        
        # Setup text
        layout = self.layout_engine.analyze_layout(text, self.logo.size, width, height)
        font_size = layout["font_size"]
        
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Break text and apply animation
        lines = self.break_text(text, font, width - 100)
        animated_lines = self.apply_animation(lines, progress)
        
        # Draw text
        self.draw_text(draw, animated_lines, font, layout, width, text_color)
        
        return np.array(img)
    
    def generate_background(self, width, height, frame_idx, total_frames):
        """Generate animated gradient background"""
        bg = np.zeros((height, width, 3), dtype=np.uint8)
        time_progress = frame_idx / total_frames
        
        for y in range(height):
            progress = y / height
            r = int(15 + progress * 100 + math.sin(time_progress * 5) * 10)
            g = int(12 + progress * 80 + math.cos(time_progress * 4) * 8)
            b = int(41 + progress * 40)
            
            bg[y, :] = [r, g, b]
        
        return bg
    
    def add_logo(self, frame, logo):
        """Add logo to top center"""
        try:
            frame_rgba = frame.convert('RGBA')
            logo_rgba = logo.convert('RGBA')
            
            # Simple logo placement at top center
            x = (frame.width - logo.width) // 2
            y = 40
            
            frame_rgba.paste(logo_rgba, (x, y), logo_rgba)
            return frame_rgba.convert('RGB')
        except:
            return frame
    
    def break_text(self, text, font, max_width):
        """Break text into lines"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            
            # Estimate width
            line_width = len(test_line) * font.size // 2
            
            if line_width > max_width:
                if len(current_line) == 1:
                    lines.append(word)
                    current_line = []
                else:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def apply_animation(self, lines, progress):
        """Apply reveal animation"""
        total_lines = len(lines)
        lines_to_show = int(total_lines * progress)
        partial_progress = (progress * total_lines) - lines_to_show
        
        revealed_lines = []
        for i in range(total_lines):
            if i < lines_to_show:
                revealed_lines.append(lines[i])
            elif i == lines_to_show:
                chars_to_show = int(len(lines[i]) * partial_progress)
                revealed_lines.append(lines[i][:chars_to_show])
            else:
                revealed_lines.append("")
        
        return revealed_lines
    
    def draw_text(self, draw, lines, font, layout, width, text_color):
        """Draw animated text"""
        start_y = layout["text_start_y"]
        line_spacing = layout["line_spacing"]
        
        # Estimate line height
        line_height = font.size * line_spacing * 1.4
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            y_pos = start_y + i * line_height
            
            # Estimate width for centering
            line_width = len(line) * font.size // 2
            x_pos = (width - line_width) // 2
            
            # Draw text
            draw.text((x_pos, y_pos), line, font=font, fill=text_color)

# ------------- Video Generation -------------
def generate_video(text, duration, width, height, text_color, output_path):
    fps = 24
    total_frames = duration * fps
    
    frame_generator = FrameGenerator()
    
    try:
        with imageio.get_writer(output_path, fps=fps, codec="libx264", quality=8) as writer:
            for frame_idx in range(total_frames):
                progress = (frame_idx + 1) / total_frames
                frame = frame_generator.create_frame(
                    text, progress, frame_idx, total_frames, width, height, text_color
                )
                writer.append_data(frame)
                
                # Update progress
                if frame_idx % 10 == 0:
                    yield frame_idx / total_frames
        
        yield 1.0
    except Exception as e:
        st.error(f"Video error: {e}")
        yield 1.0

def get_video_html(video_path):
    """Create HTML video element"""
    try:
        with open(video_path, "rb") as f:
            video_b64 = base64.b64encode(f.read()).decode()
        return f'<div class="video-container"><video controls style="width:100%"><source src="data:video/mp4;base64,{video_b64}" type="video/mp4"></video></div>'
    except:
        return '<p style="color:red">Error loading video</p>'

# ------------- Main UI -------------
def main():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;color:#ffffff'>🎬 Simple Layout Animator</h1>")
    
    # Animation Settings
    col1, col2 = st.columns(2)
    with col1:
        text_color = st.color_picker("Text Color", "#FFD700")
        duration = st.slider("Duration (seconds)", 3, 8, 5)
    with col2:
        resolution = st.selectbox("Resolution", ["720x1280", "1080x1920"], index=0)
    
    # Text Input
    sentence = st.text_area(
        "Your Text:", 
        "CREATE AMAZING CONTENT WITH SIMPLE LAYOUT OPTIMIZATION!",
        height=80,
        max_chars=200
    )
    
    # Resolution mapping
    resolution_map = {"720x1280": (720, 1280), "1080x1920": (1080, 1920)}
    W, H = resolution_map[resolution]
    
    if st.button("🚀 Generate Animation", type="primary", use_container_width=True):
        if not sentence.strip():
            st.warning("Please enter some text.")
            return
        
        with st.spinner("Generating your animation..."):
            tmpdir = Path(tempfile.mkdtemp())
            out_mp4 = tmpdir / "layout_animation.mp4"
            
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for progress in generate_video(sentence, duration, W, H, text_color, out_mp4):
                    progress_bar.progress(progress)
                    status_text.text(f"🎬 Generating: {int(progress * 100)}%")
                
                st.session_state.generated_video_path = out_mp4
                st.session_state.show_video = True
                st.session_state.video_tmpdir = tmpdir
                
                st.success("✨ Animation created!")
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    # Display video
    if hasattr(st.session_state, 'show_video') and st.session_state.show_video:
        if st.session_state.generated_video_path.exists():
            st.markdown("### 🎥 Your Animation")
            st.markdown(get_video_html(st.session_state.generated_video_path), unsafe_allow_html=True)
            
            with open(st.session_state.generated_video_path, "rb") as f:
                st.download_button(
                    "⬇️ Download MP4", 
                    f, 
                    "layout_animation.mp4", 
                    "video/mp4", 
                    use_container_width=True
                )
    
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
