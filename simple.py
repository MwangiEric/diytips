import streamlit as st
import numpy as np
import imageio
import tempfile
import base64
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import json

# Set page config
st.set_page_config(page_title="AI Typing Animation Creator", layout="centered")

# Use groq_key from secrets
groq_key = st.secrets.get("groq_key", "")

# Simple styling
st.markdown("""
<style>
.main { background: #0f0c29; }
.glass { background: rgba(255,255,255,0.1); border-radius: 16px; padding: 2rem; margin: 2rem auto; max-width: 800px; }
.video-container { margin: 2rem 0; border-radius: 12px; overflow: hidden; }
.ai-section { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; padding: 1.5rem; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

# ================================
# 🤖 Groq AI Content Generator
# ================================
class GroqContentGenerator:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def generate_diy_tips(self, topic):
        """Generate DIY tips using Groq AI"""
        if not self.api_key:
            return self.get_fallback_tips(topic)
        
        prompt = f"""
        Generate 3 practical and creative DIY tips about {topic}. 
        Each tip should be:
        - Under 120 characters
        - Practical and actionable
        - Easy to understand
        - Perfect for short video content
        
        Format as a JSON array of tips.
        Example: ["Tip 1", "Tip 2", "Tip 3"]
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": "llama-3.1-8b-instant",
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload, 
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Extract JSON from response
                try:
                    start_idx = content.find('[')
                    end_idx = content.rfind(']') + 1
                    if start_idx != -1 and end_idx != -1:
                        json_str = content[start_idx:end_idx]
                        tips = json.loads(json_str)
                        return tips
                except:
                    # Fallback: split by lines and clean
                    lines = [line.strip(' "-') for line in content.split('\n') if line.strip() and len(line.strip()) > 20]
                    return lines[:3] if lines else self.get_fallback_tips(topic)
            
            return self.get_fallback_tips(topic)
            
        except Exception as e:
            st.warning(f"AI generation failed: {e}. Using fallback tips.")
            return self.get_fallback_tips(topic)
    
    def generate_background_ideas(self, theme):
        """Generate creative background ideas using Groq AI"""
        if not self.api_key:
            return self.get_fallback_backgrounds()
        
        prompt = f"""
        Generate 3 creative geometric or vector background design ideas for a video about {theme}.
        Each idea should include:
        - Color scheme (2-3 colors)
        - Pattern style (geometric, abstract, etc.)
        - Brief description
        
        Format as JSON array with objects containing: colors, style, description.
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": "llama-3.1-8b-instant",
            "max_tokens": 400,
            "temperature": 0.8
        }
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload, 
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                try:
                    start_idx = content.find('[')
                    end_idx = content.rfind(']') + 1
                    if start_idx != -1 and end_idx != -1:
                        json_str = content[start_idx:end_idx]
                        backgrounds = json.loads(json_str)
                        return backgrounds
                except:
                    return self.get_fallback_backgrounds()
            
            return self.get_fallback_backgrounds()
            
        except:
            return self.get_fallback_backgrounds()
    
    def get_fallback_tips(self, topic):
        """Fallback DIY tips if AI fails"""
        fallback_tips = {
            "home improvement": [
                "Use vinegar and baking soda to clean stubborn stains - natural and effective!",
                "Always measure twice before cutting to avoid costly mistakes.",
                "Keep tools organized with magnetic strips for easy access and storage."
            ],
            "gardening": [
                "Water plants in the morning to reduce evaporation and prevent fungal growth.",
                "Use coffee grounds as natural fertilizer for acid-loving plants.",
                "Companion planting helps natural pest control and improves growth."
            ],
            "crafts": [
                "Repurpose old jars into stylish storage containers with a coat of paint.",
                "Use washi tape for quick and removable decorative accents around the home.",
                "Create custom stamps from potatoes for unique packaging and card designs."
            ]
        }
        
        for key, tips in fallback_tips.items():
            if key in topic.lower():
                return tips
        
        return [
            "Always wear safety glasses when working with tools - protect your vision!",
            "Keep a first aid kit handy in your workspace for quick access.",
            "Plan your project steps before starting to save time and materials."
        ]
    
    def get_fallback_backgrounds(self):
        """Fallback background ideas"""
        return [
            {
                "colors": ["#2E3192", "#1BFFFF", "#FFFFFF"],
                "style": "geometric triangles",
                "description": "Blue gradient with overlapping triangles"
            },
            {
                "colors": ["#FF512F", "#DD2476", "#000000"],
                "style": "abstract waves",
                "description": "Fiery red to pink gradient with flowing waves"
            },
            {
                "colors": ["#00B4DB", "#0083B0", "#F0F0F0"],
                "style": "minimal circles",
                "description": "Blue tones with transparent overlapping circles"
            }
        ]

# ================================
# 🎨 Background Generators
# ================================
class BackgroundGenerator:
    def __init__(self):
        self.background_types = {
            "geometric": self.geometric_background,
            "gradient": self.gradient_background,
            "abstract": self.abstract_background,
            "minimal": self.minimal_background
        }
    
    def generate_background(self, width, height, frame_idx, total_frames, style_config):
        """Generate background based on style configuration"""
        bg_type = style_config.get("type", "gradient")
        colors = style_config.get("colors", ["#0f0c29", "#302b63"])
        
        if bg_type in self.background_types:
            return self.background_types[bg_type](width, height, frame_idx, total_frames, colors)
        else:
            return self.gradient_background(width, height, frame_idx, total_frames, colors)
    
    def geometric_background(self, width, height, frame_idx, total_frames, colors):
        """Geometric pattern background"""
        bg = np.zeros((height, width, 3), dtype=np.uint8)
        time_progress = frame_idx / total_frames
        
        # Convert hex colors to RGB
        rgb_colors = [self.hex_to_rgb(color) for color in colors]
        
        # Base color
        bg[:, :] = rgb_colors[0]
        
        # Add geometric patterns
        pattern_size = 100
        for y in range(0, height, pattern_size):
            for x in range(0, width, pattern_size):
                phase = (x + y * 0.5 + time_progress * 10) % (2 * math.pi)
                
                # Alternate between colors
                color_idx = int((x // pattern_size + y // pattern_size) % len(rgb_colors))
                color = rgb_colors[color_idx]
                
                # Create geometric shapes
                for i in range(pattern_size):
                    for j in range(pattern_size):
                        xx = x + i
                        yy = y + j
                        if 0 <= xx < width and 0 <= yy < height:
                            # Triangle pattern
                            if (i + j) % pattern_size < pattern_size * (0.5 + 0.3 * math.sin(phase)):
                                bg[yy, xx] = color
        
        return bg
    
    def gradient_background(self, width, height, frame_idx, total_frames, colors):
        """Animated gradient background"""
        bg = np.zeros((height, width, 3), dtype=np.uint8)
        time_progress = frame_idx / total_frames
        
        rgb_colors = [self.hex_to_rgb(color) for color in colors]
        
        for y in range(height):
            progress = y / height
            wave = math.sin(time_progress * 5) * 10
            
            # Blend between colors
            if len(rgb_colors) == 1:
                color = rgb_colors[0]
            elif len(rgb_colors) == 2:
                color = [
                    int(rgb_colors[0][0] * (1 - progress) + rgb_colors[1][0] * progress),
                    int(rgb_colors[0][1] * (1 - progress) + rgb_colors[1][1] * progress),
                    int(rgb_colors[0][2] * (1 - progress) + rgb_colors[1][2] * progress)
                ]
            else:
                color_idx = min(int(progress * (len(rgb_colors) - 1)), len(rgb_colors) - 2)
                local_progress = (progress * (len(rgb_colors) - 1)) - color_idx
                color = [
                    int(rgb_colors[color_idx][0] * (1 - local_progress) + rgb_colors[color_idx + 1][0] * local_progress),
                    int(rgb_colors[color_idx][1] * (1 - local_progress) + rgb_colors[color_idx + 1][1] * local_progress),
                    int(rgb_colors[color_idx][2] * (1 - local_progress) + rgb_colors[color_idx + 1][2] * local_progress)
                ]
            
            for x in range(width):
                wave_effect = math.sin(x * 0.02 + time_progress * 3) * 5
                bg[y, x] = [
                    max(0, min(255, color[0] + wave + wave_effect)),
                    max(0, min(255, color[1] + wave * 0.7 + wave_effect)),
                    max(0, min(255, color[2] + wave_effect))
                ]
        
        return bg
    
    def abstract_background(self, width, height, frame_idx, total_frames, colors):
        """Abstract artistic background"""
        bg = np.zeros((height, width, 3), dtype=np.uint8)
        time_progress = frame_idx / total_frames
        
        rgb_colors = [self.hex_to_rgb(color) for color in colors]
        bg[:, :] = rgb_colors[0]
        
        # Add abstract shapes
        num_circles = 8
        for i in range(num_circles):
            radius = random.randint(50, 300)
            center_x = random.randint(0, width)
            center_y = random.randint(0, height)
            color = random.choice(rgb_colors[1:] if len(rgb_colors) > 1 else rgb_colors)
            
            for y in range(max(0, center_y - radius), min(height, center_y + radius)):
                for x in range(max(0, center_x - radius), min(width, center_x + radius)):
                    dist = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                    if dist < radius:
                        # Pulsing effect
                        pulse = (math.sin(time_progress * 4 + i) + 1) * 0.3
                        if dist < radius * (0.7 + pulse):
                            alpha = 1 - (dist / radius)
                            bg[y, x] = self.blend_colors(bg[y, x], color, alpha * 0.3)
        
        return bg
    
    def minimal_background(self, width, height, frame_idx, total_frames, colors):
        """Clean minimal background"""
        bg = np.zeros((height, width, 3), dtype=np.uint8)
        time_progress = frame_idx / total_frames
        
        rgb_colors = [self.hex_to_rgb(color) for color in colors]
        bg[:, :] = rgb_colors[0]
        
        # Add subtle lines
        line_spacing = 80
        for y in range(0, height, line_spacing):
            offset = math.sin(time_progress * 2) * 10
            line_y = y + int(offset)
            
            if 0 <= line_y < height:
                thickness = max(1, int(3 + 2 * math.sin(time_progress * 3)))
                for i in range(thickness):
                    actual_y = line_y + i
                    if 0 <= actual_y < height:
                        alpha = 0.1 + 0.1 * math.sin(time_progress * 5)
                        line_color = self.blend_colors(rgb_colors[0], rgb_colors[1] if len(rgb_colors) > 1 else (255, 255, 255), alpha)
                        bg[actual_y, :] = self.blend_colors(bg[actual_y, :], line_color, 0.3)
        
        return bg
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def blend_colors(self, color1, color2, alpha):
        """Blend two colors with alpha"""
        return [
            int(color1[0] * (1 - alpha) + color2[0] * alpha),
            int(color1[1] * (1 - alpha) + color2[1] * alpha),
            int(color1[2] * (1 - alpha) + color2[2] * alpha)
        ]

# ================================
# ✍️ Typing Animation Generator
# ================================
class TypingFrameGenerator:
    def __init__(self):
        self.logo = self.load_logo()
        self.bg_generator = BackgroundGenerator()
    
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
            img = Image.new('RGBA', (120, 60), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rectangle([5, 15, 115, 45], fill=(245, 215, 140, 180))
            draw.text((15, 20), "BRAND", fill=(0, 0, 0, 255))
            return img
    
    def create_frame(self, text, progress, frame_idx, total_frames, width, height, style_config):
        """Create frame with typing animation"""
        # Generate background
        bg_array = self.bg_generator.generate_background(width, height, frame_idx, total_frames, style_config)
        img = Image.fromarray(bg_array)
        draw = ImageDraw.Draw(img)
        
        # Add logo
        if self.logo:
            logo_x = (width - self.logo.width) // 2
            logo_y = int(height * 0.07)
            img.paste(self.logo, (logo_x, logo_y), self.logo)
        
        # Typing animation
        font_size = min(72, height // 15)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Apply typing effect
        animated_text = self.apply_typing_effect(text, font, draw, width, progress)
        
        # Draw animated text
        self.draw_animated_text(draw, animated_text, font, width, height, progress, style_config)
        
        return np.array(img)
    
    def apply_typing_effect(self, full_text, font, draw, width, progress):
        """Apply typing reveal effect"""
        max_width = int(width * 0.85)
        lines = self.wrap_text(full_text, font, max_width, draw)
        
        # Typing timeline: 70% for typing, 30% hold
        typing_duration = 0.7
        
        if progress <= typing_duration:
            typing_progress = progress / typing_duration
            total_chars = sum(len(line) for line in lines)
            chars_to_show = int(total_chars * typing_progress)
            
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
            shown_lines = lines
        
        return shown_lines
    
    def wrap_text(self, text, font, max_width, draw):
        """Wrap text to fit within max_width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
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
    
    def draw_animated_text(self, draw, lines, font, width, height, progress, style_config):
        """Draw text with typing animation"""
        text_top = int(height * 0.35)
        text_bottom = int(height * 0.85)
        text_height = text_bottom - text_top
        
        line_height = font.size * 1.6
        total_text_height = len([l for l in lines if l.strip()]) * line_height
        start_y = text_top + (text_height - total_text_height) // 2
        
        # Hold phase animation
        hold_offset = 0
        if progress > 0.7:
            hold_progress = (progress - 0.7) / 0.3
            hold_offset = 3 * math.sin(2 * math.pi * hold_progress * 2)
        
        text_color = self.hex_to_rgb(style_config.get("text_color", "#FAF5E6"))
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            y_pos = start_y + i * line_height + hold_offset
            line_width = len(line) * font.size // 2
            x_pos = (width - line_width) // 2
            
            # Text effects
            glow_color = (245, 215, 140)  # Gold light
            for dx, dy in [(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)]:
                draw.text((x_pos + dx, y_pos + dy), line, font=font, fill=glow_color)
            
            draw.text((x_pos, y_pos), line, font=font, fill=text_color)
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# ================================
# 🎬 Video Generation
# ================================
def generate_typing_video(text, duration, width, height, style_config, output_path):
    fps = 24
    total_frames = duration * fps
    generator = TypingFrameGenerator()
    
    try:
        with imageio.get_writer(output_path, fps=fps, codec="libx264", quality=8) as writer:
            for frame_idx in range(total_frames):
                progress = (frame_idx + 1) / total_frames
                frame = generator.create_frame(
                    text, progress, frame_idx, total_frames, width, height, style_config
                )
                writer.append_data(frame)
                
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
    st.markdown("<h1 style='text-align:center;color:#ffffff'>🤖 AI Typing Animation Creator</h1>")
    
    # Initialize AI Generator
    ai_generator = GroqContentGenerator(groq_key)
    
    # AI Content Generation Section
    if groq_key:
        st.markdown('<div class="ai-section">', unsafe_allow_html=True)
        st.markdown("### 🎯 AI Content Generator")
        
        col1, col2 = st.columns(2)
        with col1:
            topic = st.text_input("Enter DIY Topic:", placeholder="e.g., home organization, gardening, crafts")
            generate_content = st.button("🛠️ Generate DIY Tips")
        
        with col2:
            if generate_content and topic:
                with st.spinner("AI is generating creative tips..."):
                    tips = ai_generator.generate_diy_tips(topic)
                    if tips:
                        st.session_state.ai_tips = tips
                        st.session_state.selected_tip = tips[0]
        
        if 'ai_tips' in st.session_state:
            st.markdown("**AI-Generated Tips:**")
            selected_tip = st.radio("Choose a tip:", st.session_state.ai_tips, index=0)
            st.session_state.selected_tip = selected_tip
            
            if st.button("🎬 Use Selected Tip"):
                st.session_state.animation_text = selected_tip
                st.success("Tip loaded! Scroll down to customize animation.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Animation Settings
    with st.expander("🎨 Animation Settings", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            duration = st.slider("Duration (seconds)", 3, 8, 5)
            resolution = st.selectbox("Resolution", ["720x1280", "1080x1920"], index=0)
            text_color = st.color_picker("Text Color", "#FAF5E6")
        
        with col2:
            # Background style selection
            bg_style = st.selectbox("Background Style", 
                                  ["gradient", "geometric", "abstract", "minimal"])
            
            # AI Background Ideas
            if groq_key and st.button("🎨 Get AI Background Ideas"):
                theme = topic if 'topic' in locals() and topic else "DIY creativity"
                with st.spinner("AI is generating background ideas..."):
                    bg_ideas = ai_generator.generate_background_ideas(theme)
                    st.session_state.bg_ideas = bg_ideas
            
            if 'bg_ideas' in st.session_state:
                st.markdown("**AI Background Ideas:**")
                for i, idea in enumerate(st.session_state.bg_ideas[:2]):
                    if st.button(f"Use Idea {i+1}: {idea['style']}", key=f"bg_{i}"):
                        st.session_state.selected_bg = idea
    
    # Background color configuration
    if 'selected_bg' in st.session_state:
        bg_config = st.session_state.selected_bg
        st.info(f"Using: {bg_config['style']} - {bg_config['description']}")
    else:
        bg_config = {
            "type": bg_style,
            "colors": ["#0f0c29", "#302b63"],
            "text_color": text_color
        }
    
    # Text Input
    default_text = "Pre-drill holes before driving screws into hardwood to prevent splitting and ensure clean finishes."
    if 'animation_text' in st.session_state:
        default_text = st.session_state.animation_text
    
    text_input = st.text_area(
        "Your Text:", 
        default_text,
        height=100,
        max_chars=200
    )
    
    # Resolution mapping
    resolution_map = {"720x1280": (720, 1280), "1080x1920": (1080, 1920)}
    W, H = resolution_map[resolution]
    
    # Style configuration
    style_config = {
        "type": bg_style,
        "colors": bg_config.get("colors", ["#0f0c29", "#302b63"]),
        "text_color": text_color
    }
    
    if st.button("🚀 Generate Typing Animation", type="primary", use_container_width=True):
        if not text_input.strip():
            st.warning("Please enter some text to animate.")
            return
        
        with st.spinner("Creating your AI-powered typing animation... (30-60 seconds)"):
            tmpdir = Path(tempfile.mkdtemp())
            out_mp4 = tmpdir / "ai_typing_animation.mp4"
            
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for progress in generate_typing_video(text_input, duration, W, H, style_config, out_mp4):
                    progress_bar.progress(progress)
                    status_text.text(f"🎬 Generating: {int(progress * 100)}%")
                
                st.session_state.generated_video_path = out_mp4
                st.session_state.show_video = True
                st.session_state.video_tmpdir = tmpdir
                
                st.success("✨ AI-powered animation created!")
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    # Display video
    if hasattr(st.session_state, 'show_video') and st.session_state.show_video:
        if st.session_state.generated_video_path.exists():
            st.markdown("### 🎥 Your AI-Powered Animation")
            st.markdown(get_video_html(st.session_state.generated_video_path), unsafe_allow_html=True)
            
            with open(st.session_state.generated_video_path, "rb") as f:
                st.download_button(
                    "⬇️ Download MP4", 
                    f, 
                    "ai_typing_animation.mp4", 
                    "video/mp4", 
                    use_container_width=True
                )
    
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
