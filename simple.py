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
import json

# Set page config
st.set_page_config(page_title="AI Animation", layout="centered")

# Use groq_key from secrets
groq_key = st.secrets.get("groq_key", "")

# Remove styling, use minimal approach
st.markdown("""
<style>
.video-container { margin: 1rem 0; border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

class GroqContentGenerator:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def generate_diy_tips(self, topic):
        if not self.api_key:
            return self.get_fallback_tips(topic)
        
        prompt = f"Generate 3 practical DIY tips about {topic}. Each under 120 characters. Return as JSON array."
        
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": "llama-3.1-8b-instant",
            "max_tokens": 300,
            "temperature": 0.7
        }
        
        try:
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content'].strip()
                try:
                    start_idx = content.find('[')
                    end_idx = content.rfind(']') + 1
                    if start_idx != -1:
                        return json.loads(content[start_idx:end_idx])
                except:
                    return self.get_fallback_tips(topic)
        except:
            pass
        return self.get_fallback_tips(topic)
    
    def get_fallback_tips(self, topic):
        return [
            "Measure twice, cut once - saves time and materials.",
            "Use the right tool for the job - prevents damage and improves results.",
            "Safety first - always wear protective equipment when working."
        ]

class TypingFrameGenerator:
    def __init__(self):
        self.logo = self.load_logo()
    
    def load_logo(self):
        try:
            response = requests.get("https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037")
            logo = Image.open(io.BytesIO(response.content))
            if logo.mode != 'RGBA': logo = logo.convert('RGBA')
            return logo.resize((120, 60), Image.Resampling.LANCZOS)
        except:
            img = Image.new('RGBA', (120, 60), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rectangle([5, 15, 115, 45], fill=(245, 215, 140, 180))
            return img

    def create_frame(self, text, progress, width, height, text_color):
        # Create background
        bg = np.zeros((height, width, 3), dtype=np.uint8)
        bg[:, :] = [30, 25, 40]  # Dark background
        
        img = Image.fromarray(bg)
        draw = ImageDraw.Draw(img)
        
        # Add logo
        if self.logo:
            logo_x = (width - self.logo.width) // 2
            img.paste(self.logo, (logo_x, 40), self.logo)
        
        # Calculate text layout using pixel measurements
        font_size = self.calculate_optimal_font_size(text, width, height)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Break text into lines based on pixel width
        lines = self.break_text_to_lines(text, font, width - 100)
        
        # Apply top-to-bottom typing animation
        visible_lines = self.apply_line_animation(lines, progress)
        
        # Draw text with pixel-perfect positioning
        self.draw_text_lines(draw, visible_lines, font, width, height, text_color)
        
        return np.array(img)

    def calculate_optimal_font_size(self, text, width, height):
        # Calculate based on available space and text length
        max_font = min(80, height // 10)
        min_font = 40
        text_length = len(text)
        
        if text_length < 50:
            return max_font
        elif text_length < 100:
            return max_font - 10
        else:
            return min_font

    def break_text_to_lines(self, text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            
            # Use textbbox for accurate pixel measurement
            try:
                bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]
            except:
                line_width = len(test_line) * font.size // 1.8
            
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

    def apply_line_animation(self, lines, progress):
        """Top-to-bottom line reveal animation"""
        total_lines = len(lines)
        fully_visible_lines = int(total_lines * progress)
        partial_line_progress = (progress * total_lines) - fully_visible_lines
        
        visible_lines = []
        for i, line in enumerate(lines):
            if i < fully_visible_lines:
                # Fully visible line
                visible_lines.append(line)
            elif i == fully_visible_lines:
                # Partially visible line
                chars_to_show = int(len(line) * partial_line_progress)
                visible_lines.append(line[:chars_to_show])
            else:
                # Not yet visible
                visible_lines.append("")
        
        return visible_lines

    def draw_text_lines(self, draw, lines, font, width, height, text_color):
        """Draw text with pixel-perfect vertical centering"""
        # Calculate total text block height
        try:
            bbox = draw.textbbox((0, 0), "Test", font=font)
            line_height = bbox[3] - bbox[0] + 10
        except:
            line_height = font.size * 1.4
        
        total_text_height = len([l for l in lines if l]) * line_height
        start_y = (height - total_text_height) // 2
        
        # Draw each line
        for i, line in enumerate(lines):
            if not line:
                continue
                
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
            except:
                line_width = len(line) * font.size // 1.8
            
            x = (width - line_width) // 2
            y = start_y + (i * line_height)
            
            # Draw text with shadow for readability
            shadow_color = (30, 30, 30)
            draw.text((x + 2, y + 2), line, font=font, fill=shadow_color)
            draw.text((x, y), line, font=font, fill=text_color)

def generate_video(text, duration, width, height, text_color, output_path):
    fps = 24
    total_frames = duration * fps
    generator = TypingFrameGenerator()
    
    with imageio.get_writer(output_path, fps=fps, codec="libx264", quality=8) as writer:
        for frame_idx in range(total_frames):
            progress = (frame_idx + 1) / total_frames
            frame = generator.create_frame(text, progress, width, height, text_color)
            writer.append_data(frame)
            yield frame_idx / total_frames
    yield 1.0

def main():
    # AI Content Section
    ai_generator = GroqContentGenerator(groq_key)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if groq_key:
            topic = st.text_input("DIY Topic", placeholder="e.g., woodworking, home repair")
            if st.button("Generate Tips") and topic:
                with st.spinner("Generating..."):
                    tips = ai_generator.generate_diy_tips(topic)
                    if tips:
                        st.session_state.ai_tips = tips
                        st.session_state.selected_tip = tips[0]
        
        if 'ai_tips' in st.session_state:
            selected = st.selectbox("Select tip", st.session_state.ai_tips)
            st.session_state.animation_text = selected
    
    with col2:
        duration = st.slider("Duration", 3, 8, 5)
        resolution = st.selectbox("Resolution", ["720x1280", "1080x1920"])
        text_color = st.color_picker("Text Color", "#FAF5E6")
    
    # Text input
    default_text = st.session_state.get('animation_text', "Create professional content with optimized layouts.")
    text_input = st.text_area("Text Content", default_text, height=80)
    
    # Generate video
    if st.button("Generate Animation"):
        if not text_input.strip():
            st.warning("Enter text content")
            return
            
        W, H = (720, 1280) if resolution == "720x1280" else (1080, 1920)
        
        with st.spinner("Rendering..."):
            tmp_path = Path(tempfile.mkdtemp()) / "animation.mp4"
            
            progress_bar = st.progress(0)
            for progress in generate_video(text_input, duration, W, H, text_color, tmp_path):
                progress_bar.progress(progress)
            
            # Display result
            with open(tmp_path, "rb") as f:
                video_bytes = f.read()
                st.video(video_bytes)
                
                st.download_button(
                    "Download MP4",
                    video_bytes,
                    "animation.mp4",
                    "video/mp4",
                    use_container_width=True
                )

if __name__ == "__main__":
    main()
