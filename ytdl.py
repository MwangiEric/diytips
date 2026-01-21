#!/usr/bin/env python3
"""
Insurance Video Clip Generator - CONSOLIDATED VERSION
Merges your YouTube embed script with enhanced features:
- YouTube embed for reliable end times (kept from your script)
- Flexible input (YouTube URL or upload/paste)
- Better configuration system
- Meaningful segment analysis
- Enhanced Grok AI integration
"""

import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
import re
import json
import subprocess
import tempfile
import os
from datetime import datetime
import requests
import glob

# ----------------------------
# ENHANCED CONFIGURATION
# ----------------------------
CONFIG = {
    # AI Configuration
    'ai': {
        'provider': 'groq',
        'model': 'llama-3.3-70b-versatile',
        'api_key_env': 'GROQ_API_KEY',
        'temperature': 0.7,
        'max_tokens': 2000,
        'response_format': 'json_object'
    },
    
    # Video Configuration  
    'video': {
        'end_time_solution': 'embed',  # Your YouTube embed method
        'proxy_enabled': True,
        'proxy_config': {
            'http': 'http://udizufzc:2ile7xfmbivj@142.111.48.253:7030/',
            'https': 'http://udizufzc:2ile7xfmbivj@142.111.48.253:7030/'
        }
    },
    
    # Enhanced Insurance Keywords (from both scripts)
    'insurance': {
        'keywords': [
            'insurance', 'policy', 'coverage', 'premium', 'deductible', 'claim', 'benefits',
            'life insurance', 'health insurance', 'family', 'covered', 'protection', 'retirement',
            'inheritance', 'children', 'money', 'bankruptcy', 'living benefits', 'accident', 'illness',
            'income replacement', 'cash value', 'terminal illness', 'critical illness', 'disability',
            'living benefits', '401k', 'annuity', 'protection', 'cash value'  # From your script
        ],
        'emotional_triggers': ['family', 'children', 'protect', 'bankruptcy', 'wise', 'legacy'],
        'benefit_indicators': ['covered', 'benefits', 'money', 'income', 'cash'],
        'call_to_actions': ['should', 'need', 'must', 'why', 'get', 'join']
    },
    
    # Enhanced Prompt Templates
    'prompts': {
        'segment_analysis': """Analyze this insurance transcript and find 5-10 HIGH-VALUE clips for social media.
        
        CRITERIA:
        - Complete thoughts that make sense standalone
        - Strong emotional appeal or practical value
        - Clear insurance benefits or calls to action
        - Natural speech patterns (flexible length 3-180 seconds)
        - High engagement potential
        
        INSURANCE KEYWORDS: {keywords}
        
        RETURN JSON FORMAT:
        {{"segments": [
            {{"title": "Descriptive Title", "start": seconds, "end": seconds, 
              "hook": "Compelling hook for social media", "keywords": ["keyword1", "keyword2"],
              "confidence": 0.9, "platform": "suggested_platform"}}
        ]}}
        
        TRANSCRIPT: {transcript}""",
        
        'segment_breakdown': """Break this large insurance segment into natural sub-parts.
        Keep complete thoughts together but find natural breaking points.
        
        SEGMENT: {segment_text}
        RETURN: Natural sub-segments with time codes.""",
        
        'content_recommendation': """Recommend best use for this insurance segment:
        Platform, hook, audience, and engagement strategy.
        
        SEGMENT: {segment_text}
        Quality: {quality_score}/4"""
    }
}

# ----------------------------
# CORE FUNCTIONS (Enhanced)
# ----------------------------

def format_time_full(total_seconds: int) -> str:
    """Convert seconds to full time format"""
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def parse_time_to_seconds(time_str: str) -> int:
    """Convert time string (MM:SS or HH:MM:SS) to seconds"""
    try:
        parts = time_str.strip().split(':')
        if len(parts) == 2:  # MM:SS
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        elif len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        else:
            return int(parts[0])  # Just seconds
    except:
        return 0

def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL - from your script"""
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_transcript_with_proxy(video_id: str, use_proxy: bool = True):
    """Get transcript with proxy support"""
    try:
        if use_proxy:
            ytt_api = YouTubeTranscriptApi(
                proxy_config=GenericProxyConfig(
                    http_url=CONFIG['video']['proxy_config']['http'],
                    https_url=CONFIG['video']['proxy_config']['https']
                )
            )
        else:
            ytt_api = YouTubeTranscriptApi()
        
        transcript = ytt_api.fetch(video_id, languages=['en'])
        return transcript
        
    except Exception as e:
        st.error(f"❌ Transcript error: {str(e)}")
        return None

def get_grok_analysis(prompt):
    """Enhanced Grok analysis - from your script with improvements"""
    try:
        api_key = st.secrets.get("GROQ_API_KEY")
        if not api_key:
            st.error("❌ GROQ_API_KEY not found in secrets")
            return None
            
        client = groq.Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model=CONFIG['ai']['model'],
            messages=[{"role": "user", "content": prompt}],
            temperature=CONFIG['ai']['temperature'],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        st.error(f"AI Error: {e}")
        return None

def create_youtube_embed_link(video_id, start_time, end_time):
    """Create YouTube embed link - your reliable method"""
    return f"https://www.youtube.com/embed/{video_id}?start={int(start_time)}&end={int(end_time)}&autoplay=0&rel=0"

def analyze_insurance_content_flexible(transcript_text, insurance_keywords=None):
    """Flexible analysis that finds meaningful segments regardless of length"""
    if insurance_keywords is None:
        insurance_keywords = CONFIG['insurance']['keywords']
    
    # Parse transcript to segments
    segments = parse_transcript_to_segments(transcript_text)
    
    meaningful_segments = []
    
    for segment in segments:
        text = segment['text'].lower()
        text_keywords = [kw for kw in insurance_keywords if kw in text]
        
        # Flexible criteria - complete thoughts regardless of length
        is_complete_thought = (
            text.endswith('.') or text.endswith('!') or text.endswith('?') or
            len(text.split()) >= 5 or  # Very flexible - just 5+ words
            len(text_keywords) >= 1 or  # Has insurance content
            any(word in text[-15:] for word in ['so', 'and', 'but', 'because'])
        )
        
        if is_complete_thought:
            meaningful_segments.append({
                'start': segment['start'],
                'end': segment['start'] + 10,  # Approximate end time
                'text': segment['text'],
                'keywords': text_keywords,
                'type': 'complete_thought',
                'quality_score': len(text_keywords) + (1 if text.endswith('.') else 0)
            })
    
    return meaningful_segments

def parse_transcript_to_segments(transcript_text):
    """Parse transcript text into structured segments"""
    segments = []
    lines = transcript_text.strip().split('\n')
    
    for line in lines:
        if line.strip() and '[' in line and ']' in line:
            # Extract time and text
            time_match = re.search(r'\[(\d+):(\d+):(\d+)\]', line)
            if time_match:
                hours, minutes, seconds = map(int, time_match.groups())
                total_seconds = hours * 3600 + minutes * 60 + seconds
                
                # Extract text after time stamp
                text = line[time_match.end():].strip()
                
                segments.append({
                    'start': total_seconds,
                    'text': text,
                    'original_time': f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                })
    
    return segments

def enhance_grok_analysis(transcript_text, insurance_keywords):
    """Enhanced Grok analysis with better prompts"""
    prompt = CONFIG['prompts']['segment_analysis'].format(
        keywords=', '.join(insurance_keywords),
        transcript=transcript_text[:6000]  # First 6000 chars
    )
    
    return get_grok_analysis(prompt)

# ----------------------------
# ENHANCED STREAMLIT APP
# ----------------------------

def main():
    st.set_page_config(page_title="Enhanced Insurance Clip Generator", layout="wide", initial_sidebar_state="collapsed")
    st.title("🎯 Enhanced Insurance Clip Generator")
    st.markdown("**YouTube embed + flexible input + enhanced Grok AI + configurable system**")

    # Sidebar - Configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # AI Settings
        with st.expander("🤖 AI Settings"):
            ai_model = st.text_input("AI Model", value=CONFIG['ai']['model'])
            ai_temp = st.slider("AI Temperature", 0.0, 1.0, value=CONFIG['ai']['temperature'])
            
            if st.button("Test AI Connection"):
                test_result = get_grok_analysis("Test connection")
                if test_result:
                    st.success("✅ AI connected!")
                else:
                    st.error("❌ AI connection failed")
        
        # Video Settings
        with st.expander("📹 Video Settings"):
            st.info("✅ Using YouTube Embed for reliable end times")
            st.code("youtube.com/embed/VIDEO?start=START&end=END")
            
            proxy_enabled = st.toggle("Use Proxy", value=CONFIG['video']['proxy_enabled'])

    # Main Content
    st.header("📥 Video Input - Flexible Options")

    # Enhanced input options
    col1, col2 = st.columns([2, 1])
    with col1:
        input_method = st.radio("Choose Input Method:", ["YouTube URL", "Upload Local Video", "Paste Transcript"])
    
    with col2:
        st.info("💡 All methods work with YouTube embed for reliable end times!")

    # Input handling based on method
    video_url = None
    video_id = None
    transcript_text = None
    uploaded_file = None

    if input_method == "YouTube URL":
        col1, col2 = st.columns([3, 1])
        with col1:
            video_url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
        with col2:
            load_button = st.button("🚀 Load Transcript", type="primary")
        
        if load_button and video_url:
            with st.spinner("Loading YouTube transcript...")
                video_id = extract_video_id(video_url)
                if video_id:
                    transcript = get_transcript_with_proxy(video_id, CONFIG['video']['proxy_enabled'])
                    if transcript and hasattr(transcript, 'snippets'):
                        st.success("✅ YouTube transcript loaded!")
                        
                        # Format for analysis
                        transcript_text = ""
                        for snippet in transcript.snippets:
                            time_str = f"[{int(snippet.start//3600):02d}:{int((snippet.start%3600)//60):02d}:{int(snippet.start%60):02d}]"
                            transcript_text += f"{time_str} {snippet.text}\n"
                        
                        st.session_state['transcript_text'] = transcript_text
                        st.session_state['video_id'] = video_id
                        st.session_state['original_url'] = video_url
                        
                        # Show preview
                        with st.expander("📋 View Transcript"):
                            st.text_area("Transcript", transcript_text, height=200)
                    else:
                        st.error("❌ Could not fetch YouTube transcript")
                        st.info("💡 You can paste transcript manually below")
    
    elif input_method == "Upload Local Video":
        uploaded_file = st.file_uploader("Upload Video File", type=["mp4", "avi", "mov", "mkv"])
        if uploaded_file:
            st.success("✅ Video uploaded!")
            st.info("💡 Please paste the transcript with timestamps below")
            transcript_text = st.text_area("Paste Transcript with Timestamps", height=300, placeholder="""[00:00:00] Welcome everyone
[00:00:05] Today we're talking about insurance...""")
            if transcript_text:
                st.session_state['transcript_text'] = transcript_text
                st.session_state['uploaded_file'] = uploaded_file
    
    else:  # Paste Transcript
        transcript_text = st.text_area("Paste Transcript with Timestamps", height=400, placeholder="""[00:00:00] Welcome everyone
[00:00:05] Today we're talking about insurance
[00:00:10] For $100 or less you can get coverage...""")
        if transcript_text:
            st.session_state['transcript_text'] = transcript_text

    # Analysis Section
    if 'transcript_text' in st.session_state:
        transcript_text = st.session_state['transcript_text']
        video_id = st.session_state.get('video_id', '')
        original_url = st.session_state.get('original_url', '')
        uploaded_file = st.session_state.get('uploaded_file', None)
        
        st.header("🎯 Enhanced Insurance Segment Analysis")
        
        # Enhanced analysis button
        if st.button("🚀 Analyze with Enhanced Grok AI", type="primary"):
            with st.spinner("AI analyzing for meaningful insurance segments..."):
                result = enhance_grok_analysis(transcript_text, CONFIG['insurance']['keywords'])
                
                if result and 'segments' in result:
                    st.session_state['analysis'] = result
                    st.success(f"✅ Found {len(result['segments'])} meaningful segments!")
                else:
                    # Fallback to rule-based analysis
                    st.warning("AI analysis failed, using rule-based analysis...")
                    meaningful_segments = analyze_insurance_content_flexible(transcript_text, CONFIG['insurance']['keywords'])
                    st.session_state['analysis'] = {'segments': meaningful_segments}
                    st.success(f"✅ Found {len(meaningful_segments)} segments using rule-based analysis!")

        # Display Results
        if "analysis" in st.session_state:
            analysis = st.session_state['analysis']
            segments = analysis.get('segments', [])
            
            st.subheader("📈 Insurance Segments with YouTube Embed")
            
            for i, seg in enumerate(segments):
                with st.expander(f"🎯 Clip {i+1}: {seg.get('title', 'Insurance Clip')}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Your YouTube embed method - kept from original script
                        if video_id:
                            embed_url = create_youtube_embed_link(
                                video_id, 
                                int(seg['start']), 
                                int(seg['end'])
                            )
                            st.components.v1.iframe(embed_url, height=315)
                        else:
                            st.info("📹 Video preview available after trimming")
                        
                        st.write(f"**Text:** {seg.get('text', seg.get('hook', ''))}")
                        st.caption(f"🕐 {format_time_full(seg['start'])} - {format_time_full(seg['end'])}")
                        if seg.get('hook'):
                            st.write(f"**Hook:** {seg['hook']}")
                        if seg.get('keywords'):
                            st.caption(f"🏷️ Keywords: {', '.join(seg['keywords'][:3])}")
                    
                    with col2:
                        st.metric("Duration", f"{seg['end'] - seg['start']}s")
                        st.metric("Quality", f"{seg.get('quality_score', 0)}/4")
                        
                        # Copy embed link
                        if video_id:
                            if st.button(f"📋 Copy Embed", key=f"copy_{i}"):
                                st.code(embed_url)
                                st.success("Embed link copied!")
                        
                        # Local video trimming (if uploaded)
                        if uploaded_file and st.button(f"✂️ Trim Local Video", key=f"trim_{i}"):
                            with st.spinner("Creating local clip..."):
                                # Save and trim local video
                                with open("temp_input.mp4", "wb") as f: 
                                    f.write(uploaded_file.read())
                                
                                output_file = f"clip_{i}_{int(seg['start'])}s_to_{int(seg['end'])}s.mp4"
                                
                                # Trim using ffmpeg
                                cmd = [
                                    'ffmpeg', '-i', 'temp_input.mp4',
                                    '-ss', str(seg['start']), 
                                    '-to', str(seg['end']),
                                    '-c', 'copy',  # No re-encoding
                                    '-y', output_file
                                ]
                                
                                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                                
                                if result.returncode == 0 and os.path.exists(output_file):
                                    # Offer download
                                    with open(output_file, 'rb') as f:
                                        video_data = f.read()
                                    
                                    st.download_button(
                                        label="⬇️ Download Trimmed Clip",
                                        data=video_data,
                                        file_name=output_file,
                                        mime="video/mp4",
                                        key=f"download_{i}"
                                    )
                                    st.success("✅ Local clip created!")
                                    
                                    # Cleanup
                                    try:
                                        os.remove("temp_input.mp4")
                                        os.remove(output_file)
                                    except:
                                        pass
                                else:
                                    st.error("❌ Local trimming failed")

# Export Options
        if segments:
            st.header("📤 Export Options")
            
            export_format = st.selectbox("Export Format", ["JSON", "CSV", "MoviePy Commands"])
            
            if st.button("📥 Export All Segments"):
                export_data = {
                    'segments': segments,
                    'video_info': {
                        'video_id': video_id,
                        'original_url': original_url,
                        'method': 'youtube_embed',
                        'ai_model': CONFIG['ai']['model']
                    },
                    'export_date': datetime.now().isoformat()
                }
                
                if export_format == "JSON":
                    st.download_button(
                        label="⬇️ Download JSON",
                        data=json.dumps(export_data, indent=2),
                        file_name=f"insurance_segments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                
                elif export_format == "CSV":
                    csv_data = "Clip,Title,Start,End,Duration,Hook,Keywords,Quality\n"
                    for i, seg in enumerate(segments):
                        csv_data += f"{i+1},\"{seg.get('title', '')}\",{seg['start']},{seg['end']},{seg['end']-seg['start']},\"{seg.get('hook', '')}\",\"{' '.join(seg.get('keywords', [])[:3])}\",{seg.get('quality_score', 0)}\n"
                    
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv_data,
                        file_name=f"insurance_segments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                )
                
                else:  # MoviePy Commands
                    commands = "# MoviePy Commands for Insurance Clips\n\n"
                    for i, seg in enumerate(segments):
                        commands += f"# Clip {i+1}: {seg.get('title', 'Clip')}\n"
                        commands += f"clip_{i} = VideoFileClip('your_video.mp4').subclip({seg['start']}, {seg['end']})\n"
                        commands += f"clip_{i}.write_videofile('clip_{i}_{int(seg['start'])}s_to_{int(seg['end'])}s.mp4')\n\n"
                    
                    st.download_button(
                        label="⬇️ Download Commands",
                        data=commands,
                        file_name=f"moviepy_commands_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py",
                        mime="text/plain"
                )

# FOOTER
st.markdown("---")
st.caption("🎯 Enhanced Insurance Clip Generator • YouTube Embed • Flexible Input • Enhanced Grok AI")
st.caption("✅ Keeps: Your YouTube embed method • Enhanced: Better prompts, flexible input, configuration system")

if __name__ == "__main__":
    main()
