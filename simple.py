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
st.set_page_config(page_title="Typing Animation Creator", layout="centered")

# Simple styling
st.markdown("""
<style>
.main { background: #0f0c29; }
.glass { background: rgba(255,255,255,0.1); border-radius: 16px; padding: 2rem; margin: 2rem auto; max-width: 800px; }
.video-container { margin: 2rem 0; border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ================================
# 🎨 Brand Colors (from your concept)
# ================================
GOLD_LIGHT = (245, 215, 140)
ESPRESSO = (45, 38, 30)
TEXT_COLOR = (250, 245, 230)

# ================================
# ✍️ Text Wrapping Function
# ================================
def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        
        # Estimate width (simpler than textbbox for compatibility)
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

# ================================
# 🖼️ Background Generator
# ================================
def create_background(width, height, time_progress):
    """Create animated background with waves"""
    bg = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Base espresso color
    bg[:, :] = [ESPRESSO[0], ESPRESSO[1], ESPRESSO[2]]
    
    # Add gold wave lines
    for y in range(0, height, 25):
        phase = (y * 0.04 + time_progress * 2) % (2 * math.pi)
        opacity = int(25 * (1 + math.sin(phase)) / 2)
        wave_y = y + 3 * math.sin(phase)
        
        if 0 <= wave_y < height:
            # Blend gold color with background
            for x in range(width):
                if x % 2 == 0:  # Optimize performance
                    bg[int(wave_y), x] = [
                        min(255, ESPRESSO[0] + GOLD_LIGHT[0] * opacity // 255),
                        min(255, ESPRESSO[1] + GOLD_LIGHT[1] * opacity // 255),
                        min(255, ESPRESSO[2] + GOLD_LIGHT[2] * opacity // 255)
                    ]
    
    return bg

# ================================
# 🎞️ Frame Generator with Typing Effect
# ================================
class TypingFrameGenerator:
    def __init__(self):
        self.logo = self.load_logo()
    
    def load_logo(self):
        """Load logo from URL with fallback"""
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
            draw.rectangle([5, 15, 115, 45], fill=(*GOLD_LIGHT, 180))
            draw.text((15, 20), "BRAND", fill=(0, 0, 0, 255))
            return img
    
    def create_frame(self, text, progress, frame_idx, total_frames, width, height):
        """Create frame with typing animation"""
        # Generate background
        time_progress = frame_idx / total_frames
        bg_array = create_background(width, height, time_progress)
        img = Image.fromarray(bg_array)
        draw = ImageDraw.Draw(img)
        
        # Add logo
        if self.logo:
            logo_x = (width - self.logo.width) // 2
            logo_y = int(height * 0.07)
            img.paste(self.logo, (logo_x, logo_y), self.logo)
        
        # Typing animation logic
        font_size = min(72, height // 15)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Apply typing effect
        animated_text = self.apply_typing_effect(text, font, draw, width, progress)
        
        # Draw the animated text
        self.draw_animated_text(draw, animated_text, font, width, height, progress)
        
        return np.array(img)
    
    def apply_typing_effect(self, full_text, font, draw, width, progress):
        """Apply typing reveal effect to text"""
        max_width = int(width * 0.85)
        
        # First, wrap the full text to get line structure
        lines = wrap_text(full_text, font, max_width, draw)
        
        # Typing timeline: 70% for typing, 30% hold
        typing_duration = 0.7
        hold_duration = 0.3
        
        if progress <= typing_duration:
            # Calculate how much text to reveal
            typing_progress = progress / typing_duration
            total_chars = sum(len(line) for line in lines)
            chars_to_show = int(total_chars * typing_progress)
            
            # Rebuild text with partial reveal
            shown_lines = []
            chars_used = 0
            for line in lines:
                if chars_used >= chars_to_show:
                    shown_lines.append("")
                    continue
                    
                remaining_chars = chars_to_show - chars_used
                if remaining_chars >= len(line):
                    shown_lines.append(line)
                    chars_used += len(line)
                else:
                    shown_lines.append(line[:remaining_chars])
                    chars_used = chars_to_show
        else:
            # Hold phase - show all text with subtle animation
            shown_lines = lines
        
        return shown_lines
    
    def draw_animated_text(self, draw, lines, font, width, height, progress):
        """Draw text with typing animation and effects"""
        # Safe text area (avoid top logo & bottom)
        text_top = int(height * 0.35)
        text_bottom = int(height * 0.85)
        text_height = text_bottom - text_top
        
        # Calculate vertical positioning
        line_height = font.size * 1.6  # Increased spacing for readability
        total_text_height = len([l for l in lines if l.strip()]) * line_height
        start_y = text_top + (text_height - total_text_height) // 2
        
        # Hold phase animation (subtle float)
        hold_offset = 0
        if progress > 0.7:  # Hold phase
            hold_progress = (progress - 0.7) / 0.3
            hold_offset = 3 * math.sin(2 * math.pi * hold_progress * 2)
        
        # Draw each line
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            y_pos = start_y + i * line_height + hold_offset
            
            # Estimate width for centering
            line_width = len(line) * font.size // 2
            x_pos = (width - line_width) // 2
            
            # Text glow effect
            glow_color = (*GOLD_LIGHT, 180)
            for dx, dy in [(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)]:
                draw.text((x_pos + dx, y_pos + dy), line, font=font, fill=glow_color)
            
            # Main text
            draw.text((x_pos, y_pos), line, font=font, fill=TEXT_COLOR)

# ================================
# 🎬 Video Generation
# ================================
def generate_typing_video(text, duration, width, height, output_path):
    """Generate video with typing animation"""
    fps = 24
    total_frames = duration * fps
    
    generator = TypingFrameGenerator()
    
    try:
        with imageio.get_writer(output_path, fps=fps, codec="libx264", quality=8) as writer:
            for frame_idx in range(total_frames):
                progress = (frame_idx + 1) / total_frames
                frame = generator.create_frame(
                    text, progress, frame_idx, total_frames, width, height
                )
                writer.append_data(frame)
                
                # Update progress
                if frame_idx % 10 == 0:
                    yield frame_idx / total_frames
        
        yield 1.0
    except Exception as e:
        st.error(f"Video generation error: {e}")
        yield 1.0

def get_video_html(video_path):
    """Create HTML video element"""
    try:
        with open(video_path, "rb") as f:
            video_b64 = base64.b64encode(f.read()).decode()
        return f'<div class="video-container"><video controls style="width:100%"><source src="data:video/mp4;base64,{video_b64}" type="video/mp4"></video></div>'
    except:
        return '<p style="color:red">Error loading video</p>'

# ================================
# 🌐 Streamlit App
# ================================
def main():
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;color:#ffffff'>✍️ Typing Animation Creator</h1>")
    st.markdown("<div style='text-align:center;color:#cccccc'>Text appears as if being typed — perfect for social media!</div>", unsafe_allow_html=True)
    
    # Settings
    col1, col2 = st.columns(2)
    with col1:
        duration = st.slider("Duration (seconds)", 3, 10, 6)
        resolution = st.selectbox("Resolution", ["720x1280", "1080x1920"], index=0)
    
    with col2:
        show_logo = st.checkbox("Show Brand Logo", True)
        preview_mode = st.checkbox("Fast Preview (lower quality)", False)
    
    # Text Input
    default_text = "Pre-drill holes before driving screws into hardwood to prevent splitting and ensure clean professional finishes."
    text_input = st.text_area(
        "Your Text:", 
        default_text,
        height=100,
        max_chars=300,
        help="Keep it under 300 characters for best results"
    )
    
    # Resolution mapping
    resolution_map = {"720x1280": (720, 1280), "1080x1920": (1080, 1920)}
    W, H = resolution_map[resolution]
    
    if st.button("🎬 Generate Typing Animation", type="primary", use_container_width=True):
        if not text_input.strip():
            st.warning("Please enter some text to animate.")
            return
        
        with st.spinner("Creating your typing animation... (this may take 30-60 seconds)"):
            tmpdir = Path(tempfile.mkdtemp())
            out_mp4 = tmpdir / "typing_animation.mp4"
            
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Adjust quality for preview
                quality = 6 if preview_mode else 8
                
                for progress in generate_typing_video(text_input, duration, W, H, out_mp4):
                    progress_bar.progress(progress)
                    status_text.text(f"🎬 Typing Animation: {int(progress * 100)}%")
                
                st.session_state.generated_video_path = out_mp4
                st.session_state.show_video = True
                st.session_state.video_tmpdir = tmpdir
                
                st.success("✨ Typing animation created!")
                
            except Exception as e:
                st.error(f"❌ Error generating video: {e}")
    
    # Display video
    if hasattr(st.session_state, 'show_video') and st.session_state.show_video:
        if st.session_state.generated_video_path.exists():
            st.markdown("### 🎥 Your Typing Animation")
            st.markdown(get_video_html(st.session_state.generated_video_path), unsafe_allow_html=True)
            
            with open(st.session_state.generated_video_path, "rb") as f:
                st.download_button(
                    "⬇️ Download MP4", 
                    f, 
                    "typing_animation.mp4", 
                    "video/mp4", 
                    use_container_width=True,
                    help="Perfect for Instagram Reels, TikTok, or YouTube Shorts"
                )
    
    # Tips section
    with st.expander("💡 Pro Tips"):
        st.markdown("""
        - **Short & Sweet**: 80-150 characters work best
        - **Clear Messages**: One main idea per animation
        - **DIY Tips**: Perfect for step-by-step tutorials
        - **Quote Cards**: Great for inspirational quotes
        - **Product Features**: Highlight key benefits
        """)
    
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
