import streamlit as st
from moviepy.editor import *
import requests
from PIL import Image
import numpy as np
import io
import zipfile
import os
import time

# Page config for mobile-first WhatsApp sharing
st.set_page_config(
    page_title="254 Video Factory", 
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional broker dashboard
st.markdown("""
    <style>
    .main-header { font-size: 3rem; color: #1E3A8A; }
    .metric-card { background: linear-gradient(135deg, #1E3A8A 0%, #10B981 100%); }
    </style>
""", unsafe_allow_html=True)

class Video254Factory:
    def __init__(self):
        self.poster_url = "https://your-app.vercel.app/api/og/254-poster"  # UPDATE THIS
    
    def load_poster(self):
        """Load the static OG poster background"""
        try:
            response = requests.get(self.poster_url, timeout=10)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
            return ImageClip(np.array(img)).resize((1080, 1920))  # WhatsApp Status size
        except Exception as e:
            st.error(f"Poster load failed: {e}")
            return None
    
    def animate_text(self, text: str, animation: str, duration: float = 6.0):
        """Create animated text overlay with multiple effects"""
        txt_clip = TextClip(
            text, 
            fontsize=80,
            color='#F59E0B',
            font='Arial-Bold',
            stroke_color='black',
            stroke_width=3,
            size=(900, None),
            method='caption'
        ).set_duration(duration)
        
        # Apply animation effects
        if animation == "slideup":
            txt_clip = txt_clip.set_position(lambda t: ('center', 500 + 800 * t))
        elif animation == "slideleft":
            txt_clip = txt_clip.set_position(lambda t: (-400 + 500 * t, 'center'))
        elif animation == "fadebounce":
            txt_clip = txt_clip.fadein(1).fadeout(1).fx(vfx.bounceIn, 1.5)
        elif animation == "typewriter":
            txt_clip = self.typewriter_effect(txt_clip, duration)
        elif animation == "pulse":
            txt_clip = txt_clip.fx(vfx.colorx, lambda t: 1 + 0.1 * np.sin(3 * t))
        
        return txt_clip.set_position(('center', 600))
    
    def typewriter_effect(self, clip, duration):
        """Typewriter text animation"""
        txt = clip.text
        txt_len = len(txt)
        
        def make_frame(t):
            chars = int(txt_len * min(t / (duration * 0.7), 1))
            partial_text = txt[:chars] + " " * max(0, txt_len - chars)
            return TextClip(partial_text, **clip.last_draw_params).img
        
        return clip.fl(make_frame, duration)
    
    def generate_video_pack(self, messages: list, animations: list):
        """Generate complete video pack for WhatsApp broadcast"""
        poster = self.load_poster()
        if not poster:
            return None
        
        video_files = []
        
        for i, (message, anim) in enumerate(zip(messages, animations)):
            # Animate text over poster
            text_clip = self.animate_text(message, anim)
            
            # Composite video
            final_video = CompositeVideoClip([poster.set_duration(6), text_clip])
            
            # Export optimized for WhatsApp Status
            output_path = f"254_video_{i+1}.mp4"
            final_video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio=False,
                preset='ultrafast',
                threads=4,
                logger=None
            )
            video_files.append(output_path)
            
            # Preview first video
            if i == 0:
                st.video(output_path)
        
        return video_files

# === STREAMLIT UI ===
st.markdown('<h1 class="main-header">🎬 254 Insurance Video Factory</h1>', unsafe_allow_html=True)
st.markdown("**Bilha · Generate WhatsApp Status videos in 3 clicks**")

# Sidebar controls
st.sidebar.header("📱 Video Settings")
tab1, tab2 = st.tabs(["Quick Generate", "Bulk Pack"])

with tab1:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        message = st.text_area(
            "Video Message", 
            "KSh4,200/mo → KSh5M Family Protection
Flexible Premiums · Jubilee Faida Elite",
            height=100
        )
    
    with col2:
        animation = st.selectbox("Animation", [
            "slideup", "slideleft", "fadebounce", 
            "typewriter", "pulse"
        ])
    
    if st.button("🎥 Generate Video", type="primary", use_container_width=True):
        with st.spinner("Creating professional 6-second video..."):
            factory = Video254Factory()
            poster = factory.load_poster()
            
            if poster:
                text_clip = factory.animate_text(message, animation)
                final_video = CompositeVideoClip([poster.set_duration(6), text_clip])
                
                output_path = "254_preview.mp4"
                final_video.write_videofile(output_path, fps=24, codec='libx264', 
                                          audio=False, preset='ultrafast')
                
                st.success("✅ Video ready!")
                st.video(output_path)
                with open(output_path, "rb") as f:
                    st.download_button(
                        "💾 Download MP4", f, "254_insurance_video.mp4",
                        "video/mp4", use_container_width=True
                    )

with tab2:
    st.header("📦 Bulk Video Pack (5 videos)")
    
    # Predefined insurance messages
    default_messages = [
        "MYTH: Life insurance is too expensive",
        "FACT: KSh4,200/mo = KSh5M protection", 
        "Jubilee Faida Elite - Flexible payments",
        "Lock rates NOW before they triple",
        "Protect your family today"
    ]
    
    messages = []
    for i in range(5):
        msg = st.text_input(f"Video {i+1}", default_messages[i] if i < len(default_messages) else "")
        if msg:
            messages.append(msg)
    
    anims = st.multiselect("Animations", [
        "slideup", "slideleft", "fadebounce", "typewriter", "pulse"
    ], default=["slideup", "slideleft", "fadebounce", "typewriter", "pulse"])
    
    if st.button("🚀 Generate 5-Video Pack", type="secondary", use_container_width=True) and len(messages) >= 3:
        with st.spinner("Generating complete WhatsApp pack..."):
            factory = Video254Factory()
            videos = factory.generate_video_pack(messages[:5], anims[:5])
            
            if videos:
                zip_path = "254_video_pack.zip"
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for video in videos:
                        zipf.write(video, os.path.basename(video))
                        os.remove(video)
                
                st.success(f"✅ Pack ready! {len(videos)} videos for 50 agents")
                with open(zip_path, "rb") as f:
                    st.download_button(
                        "📱 WhatsApp Pack (ZIP)", f, zip_path,
                        "application/zip", use_container_width=True
                    )

# Footer metrics
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Videos Today", "0")
with col2: st.metric("Top Agent", "Bilha")
with col3: st.metric("Clients Month", "15")
with col4: st.metric("Impressions", "2,500+")

st.markdown("---")
st.caption("🎯 Send to WhatsApp Status → 50 agents → 2,500 daily impressions | IRA Compliant")