import streamlit as st
import requests
import cv2
import numpy as np
from moviepy.editor import VideoFileClip
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
from PIL import Image, ImageDraw
import textwrap
import re
import io
from groq import Groq

# ----------------------------
# CONFIGURATION
# ----------------------------
PROXY_CONFIG = {
    'http': 'http://udizufzc:2ile7xfmbivj@142.111.48.253:7030/',
    'https': 'http://udizufzc:2ile7xfmbivj@142.111.48.253:7030/'
}

# ----------------------------
# CORE FUNCTIONS
# ----------------------------
def extract_video_id(url: str) -> str:
    patterns = [
        r'youtube\.com/shorts/([^?&]+)',
        r'youtube\.com/watch\?v=([^?&]+)',
        r'youtu\.be/([^?&]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url

def get_transcript_with_proxy(video_id: str):
    try:
        proxy_config = GenericProxyConfig(
            http_url=PROXY_CONFIG['http'],
            https_url=PROXY_CONFIG['https']
        )
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=['en'], proxy_config=proxy_config)
        return transcript
    except Exception as e:
        st.error(f"❌ Transcript error: {e}")
        return []

def create_segment_links(video_id: str, segments: list) -> list:
    """Create clickable YouTube segment links"""
    links = []
    for seg in segments:
        start_time = int(seg['start'])
        end_time = int(seg['end'])
        
        # YouTube URL with start and end parameters
        youtube_url = f"https://www.youtube.com/watch?v={video_id}&start={start_time}&end={end_time}"
        
        # Format time for display
        start_str = f"{start_time//60}:{start_time%60:02d}"
        end_str = f"{end_time//60}:{end_time%60:02d}"
        
        links.append({
            'url': youtube_url,
            'start_time': start_time,
            'end_time': end_time,
            'duration': end_time - start_time,
            'display_time': f"{start_str} - {end_str}",
            'text': seg['text'],
            'score': seg.get('score', 0)
        })
    
    return links

def create_visual_segment_card(segment: dict, video_id: str, index: int) -> None:
    """Create a visual card for a segment with YouTube link"""
    with st.container():
        col1, col2, col3 = st.columns([1, 4, 1])
        
        with col1:
            st.markdown(f"### {index}")
            st.metric("Score", f"{segment.get('score', 0):.1f}")
        
        with col2:
            st.markdown(f"**{segment['text']}**")
            st.caption(f"⏰ {segment['display_time']} ({segment['duration']}s)")
            
            # Create columns for buttons
            btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 1])
            
            with btn_col1:
                # YouTube link button
                st.markdown(f"[▶️ Watch on YouTube]({segment['url']})", unsafe_allow_html=True)
            
            with btn_col2:
                # Copy link button
                if st.button(f"📋 Copy Link {index}", key=f"copy_{index}"):
                    st.code(segment['url'])
                    st.success("Link copied!")
            
            with btn_col3:
                # Visualize button
                if st.button(f"🎨 Visualize {index}", key=f"viz_{index}"):
                    st.session_state['selected_segment'] = segment

        with col3:
            # Duration badge
            st.info(f"{segment['duration']}s")

def suggest_trim_times(transcript: list, min_duration: int = 10) -> list:
    """Suggest best segments to trim based on insight + duration"""
    segments = []
    insight_keywords = ['important', 'key', 'lesson', 'advice', 'insight', 'wisdom', 'perspective']
    
    for segment in transcript:
        text = segment.text.strip()
        duration = segment.duration
        
        if duration < min_duration:
            continue
        
        insight_score = sum(text.lower().count(kw) for kw in insight_keywords)
        completeness_score = text.count('.') + text.count('!') + text.count('?')
        duration_score = min(duration / 30, 1.0)
        
        total_score = insight_score * 2 + completeness_score + duration_score * 5
        
        segments.append({
            'text': text,
            'start': segment.start,
            'end': segment.start + segment.duration,
            'duration': segment.duration,
            'score': total_score
        })
    
    segments.sort(key=lambda x: x['score'], reverse=True)
    return segments[:10]  # Return top 10 for user selection

def analyze_with_groq(content: str, analysis_type: str = "comprehensive") -> dict:
    """Analyze content using Groq AI"""
    if not st.secrets.get("groq_key"):
        return {"error": "Groq API key not found in secrets"}
    
    try:
        client = Groq(api_key=st.secrets["groq_key"])
        
        if analysis_type == "comprehensive":
            prompt = f"""Analyze this parenting/transcript content comprehensively:
            
            Content: {content[:2000]}
            
            Return JSON format:
            {{
                "summary": "Brief summary",
                "key_themes": ["theme1", "theme2"],
                "emotional_tone": "tone description",
                "advice_extracted": ["advice1", "advice2"],
                "parenting_insights": ["insight1", "insight2"],
                "recommendations": ["rec1", "rec2"],
                "suitability_score": 0-100
            }}"""
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        return {"error": str(e)}

# ----------------------------
# STREAMLIT APP
# ----------------------------
st.set_page_config(page_title="YouTube Visual + Groq Toolkit", layout="wide", initial_sidebar_state="collapsed")
st.title("🎬 YouTube Visual + Groq Toolkit")
st.markdown("**Extract • Analyze • Visualize • AI-Powered** with proxy support")

# Sidebar
with st.sidebar:
    st.header("🔧 Configuration")
    if st.secrets.get("groq_key"):
        st.success("✅ Groq API: Connected")
    else:
        st.warning("⚠️ Add `groq_key` to Streamlit secrets")

# MAIN APP
tab1, tab2, tab3, tab4 = st.tabs(["📥 Extract & Analyze", "✂️ Smart Clips", "🖼️ Visual Content", "🧠 Groq AI Analysis"])

# TAB 1: EXTRACT & ANALYZE
with tab1:
    st.header("📥 Extract & Analyze")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    
    with col2:
        if st.button("🚀 Analyze", type="primary"):
            if url:
                with st.spinner("Analyzing with proxy..."):
                    video_id = extract_video_id(url)
                    transcript = get_transcript_with_proxy(video_id)
                    
                    if transcript:
                        st.success("✅ Transcript extracted!")
                        st.session_state['transcript'] = transcript
                        st.session_state['video_id'] = video_id
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Total Segments", len(transcript))
                            st.metric("Total Duration", f"{transcript[-1].start + transcript[-1].duration:.1f}s")
                        
                        with col_b:
                            quotes = []
                            insight_keywords = ['important', 'key', 'crucial', 'lesson', 'advice', 'insight', 'wisdom', 'perspective']
                            for segment in transcript:
                                text = segment.text.strip()
                                score = sum(text.lower().count(kw) for kw in insight_keywords)
                                if 20 < len(text) < 120 and score > 0:
                                    quotes.append({
                                        'text': text,
                                        'start': segment.start,
                                        'duration': segment.duration,
                                        'score': score
                                    })
                            quotes.sort(key=lambda x: x['score'], reverse=True)
                            st.metric("Insightful Quotes", len(quotes[:5]))
                        
                        if quotes:
                            st.subheader("🎯 Top Insightful Quotes")
                            for i, quote in enumerate(quotes[:5], 1):
                                with st.expander(f"Quote {i} - Score: {quote['score']}"):
                                    st.write(f"**{quote['text']}**")
                                    st.caption(f"⏰ {quote['start']:.1f}s - [Watch](https://www.youtube.com/watch?v={video_id}&t={int(quote['start'])}s)")

# TAB 2: SMART CLIPS WITH YOUTUBE LINKS
with tab2:
    st.header("✂️ Smart Clip Suggestions with YouTube Links")
    
    if 'transcript' not in st.session_state:
        st.info("💡 Analyze a video first to see clip suggestions")
    else:
        transcript = st.session_state['transcript']
        video_id = st.session_state.get('video_id', '')
        
        if transcript and video_id:
            min_duration = st.slider("Minimum clip duration (seconds)", 5, 60, 15)
            
            if st.button("🎯 Find Best Clips"):
                with st.spinner("Finding optimal clips..."):
                    segments = suggest_trim_times(transcript, min_duration)
                    segment_links = create_segment_links(video_id, segments)
                    
                    st.subheader("🎯 Recommended Clips (Click to Watch!)")
                    st.info("📍 Click the YouTube links to watch specific segments")
                    
                    for i, link in enumerate(segment_links, 1):
                        create_visual_segment_card(link, video_id, i)
                    
                    # Summary stats
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Segments Found", len(segment_links))
                    with col2:
                        avg_duration = sum(seg['duration'] for seg in segment_links) / len(segment_links) if segment_links else 0
                        st.metric("Average Duration", f"{avg_duration:.1f}s")
                    with col3:
                        best_score = max([seg['score'] for seg in segment_links]) if segment_links else 0
                        st.metric("Best Score", f"{best_score:.1f}")

# TAB 3: VISUAL CONTENT
with tab3:
    st.header("🖼️ Visual Content Creation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Quote to OG Image")
        if 'transcript' in st.session_state:
            transcript = st.session_state['transcript']
            quotes = []
            insight_keywords = ['important', 'key', 'crucial', 'lesson', 'advice', 'insight', 'wisdom', 'perspective']
            for segment in transcript:
                text = segment.text.strip()
                score = sum(text.lower().count(kw) for kw in insight_keywords)
                if 20 < len(text) < 120 and score > 0:
                    quotes.append({'text': text, 'score': score})
            quotes.sort(key=lambda x: x['score'], reverse=True)
            
            if quotes:
                selected_quote = st.selectbox("Select a quote", [q['text'] for q in quotes[:5]])
                if st.button("Generate OG Image", type="primary"):
                    og_image = create_og_image(selected_quote)
                    st.image(og_image, caption="Social Media Ready", use_column_width=True)
                    st.download_button("📥 Download OG Image", og_image, "og_image.png", "image/png")
    
    with col2:
        st.subheader("Custom Visual")
        custom_text = st.text_area("Enter text for visual", "Your teen is listening, even when they seem to ignore you.")
        if st.button("Generate Visual"):
            visual = create_og_image(custom_text, "Custom Message")
            st.image(visual, caption="Visual Content", use_column_width=True)
            st.download_button("📥 Download Visual", visual, "custom_visual.png", "image/png")

# FOOTER
st.markdown("---")
st.caption("🔧 Powered by YouTube Transcript API + MoviePy + Groq + Streamlit | Proxy: Webshare")

# Add some helpful instructions at the bottom
with st.expander("📖 How to Use"):
    st.markdown("""
    ### Quick Guide:
    1. **Paste YouTube URL** → Click "Analyze"
    2. **View Segments** → Click YouTube links to watch specific parts
    3. **Select Clips** → Use "Watch on YouTube" buttons
    4. **Copy Links** → Use "Copy Link" for sharing
    5. **Generate Visuals** → Create images from quotes
    6. **AI Analysis** → Get Groq-powered insights
    
    ### Features:
    - ✅ Proxy-enabled YouTube access
    - ✅ Clickable YouTube segment links
    - ✅ Visual segment cards
    - ✅ AI-powered analysis
    - ✅ Direct YouTube integration
    """)
