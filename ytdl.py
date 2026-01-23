#!/usr/bin/env python3
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import re
import json
import groq
from datetime import datetime

# ----------------------------
# CONFIGURATION
# ----------------------------
CONFIG = {
    'ai': {
        'model': 'llama-3.3-70b-versatile',
        'temperature': 0.7,
    },
    'video': {
        'proxy_enabled': True,
        'proxy_config': {
            'http': 'http://udizufzc:2ile7xfmbivj@142.111.48.253:7030/',
            'https': 'http://udizufzc:2ile7xfmbivj@142.111.48.253:7030/'
        }
    },
    'insurance': {
        'keywords': [
            'insurance', 'policy', 'coverage', 'premium', 'deductible', 'claim', 'benefits',
            'life insurance', 'health insurance', 'family', 'covered', 'protection', 'retirement',
            'inheritance', 'children', 'money', 'bankruptcy', 'living benefits', 'accident', 'illness',
            'income replacement', 'cash value', 'terminal illness', 'critical illness', 'disability',
            '401k', 'annuity'
        ],
    },
    'prompts': {
        'segment_analysis': """Analyze this insurance transcript for all high-value social media segments. 

INSTRUCTIONS:
- Do not limit the number of segments; identify every distinct valuable thought.
- Capture 'Nested Clips': If a long educational segment contains a shorter, punchy 'viral hook' within it, identify both as separate segments.
- Segments can overlap if they serve different content purposes (e.g., a 30s Reel vs. a 2-minute YouTube Short).
- Focus on emotional triggers, clear insurance explanations, and strong calls to action.

RETURN JSON FORMAT ONLY:
{{
  "segments": [
    {{
      "title": "Descriptive Title", 
      "start": seconds, 
      "end": seconds, 
      "hook": "Social Media Hook", 
      "keywords": [], 
      "type": "Micro/Macro", 
      "confidence_score": 0.9
    }}
  ]
}}

TRANSCRIPT: {transcript}"""
    }
}

# ----------------------------
# CORE LOGIC
# ----------------------------

def extract_video_id(url: str) -> str:
    pattern = r'(?:v=|\/|be\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_transcript_with_proxy(video_id: str):
    try:
        if CONFIG['video']['proxy_enabled']:
            return YouTubeTranscriptApi.get_transcript(video_id, proxies=CONFIG['video']['proxy_config'])
        return YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        st.error(f"❌ Transcript error: {str(e)}")
        return None

def get_grok_analysis(prompt):
    try:
        api_key = st.secrets.get("groq_key")
        if not api_key:
            st.error("❌ 'groq_key' not found in Streamlit secrets")
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

def parse_raw_text_to_segments(text):
    """Parses text with [HH:MM:SS] timestamps into list of dicts"""
    segments = []
    lines = text.strip().split('\n')
    for line in lines:
        time_match = re.search(r'\[(\d+):(\d+):(\d+)\]', line)
        if time_match:
            h, m, s = map(int, time_match.groups())
            total_seconds = h * 3600 + m * 60 + s
            content = line[time_match.end():].strip()
            segments.append({'start': total_seconds, 'text': content, 'original_time': f"{h:02d}:{m:02d}:{s:02d}"})
    return segments

def rule_based_fallback(transcript_text):
    """Sequential fallback with look-ahead timing"""
    segments = parse_raw_text_to_segments(transcript_text)
    results = []
    keywords = CONFIG['insurance']['keywords']
    
    for i in range(len(segments)):
        current = segments[i]
        # End at next timestamp start or +10s if last
        end_time = segments[i+1]['start'] - 0.5 if i < len(segments)-1 else current['start'] + 10.0
        
        text_lower = current['text'].lower()
        found_kw = [kw for kw in keywords if kw in text_lower]
        
        if found_kw or len(text_lower.split()) > 6:
            results.append({
                'title': f"Insurance Insight at {current['original_time']}",
                'start': current['start'],
                'end': end_time,
                'text': current['text'],
                'keywords': found_kw,
                'type': 'Sequential'
            })
    return {'segments': results}

def format_time(seconds):
    seconds = int(seconds)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"

# ----------------------------
# STREAMLIT UI
# ----------------------------

def main():
    st.set_page_config(page_title="Insurance Content Miner", layout="wide")
    st.title("🎯 Insurance Clip Content Miner")
    st.markdown("Extract unlimited high-value segments for social media.")

    # 1. Inputs
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("1. Video Source (For Preview)")
        video_url = st.text_input("YouTube URL", placeholder="Used for embedding clips...")
        v_id = extract_video_id(video_url)
        if v_id:
            st.session_state['video_id'] = v_id
            st.success(f"Video Loaded: {v_id}")

    with col_b:
        st.subheader("2. Transcript (For Analysis)")
        transcript_input = st.text_area("Paste Transcript with [HH:MM:SS]", height=150, help="Even if using a URL, you can paste a custom transcript here.")
        
        if st.button("Fetch YouTube Transcript") and v_id:
            data = get_transcript_with_proxy(v_id)
            if data:
                formatted = ""
                for e in data:
                    s = int(e['start'])
                    ts = f"[{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}]"
                    formatted += f"{ts} {e['text']}\n"
                transcript_input = formatted
                st.session_state['working_transcript'] = formatted
                st.rerun()

    if transcript_input:
        st.session_state['working_transcript'] = transcript_input

    # 2. Action
    if 'working_transcript' in st.session_state:
        if st.button("🚀 Analyze Content", type="primary"):
            with st.spinner("Grok is mining segments..."):
                prompt = CONFIG['prompts']['segment_analysis'].format(transcript=st.session_state['working_transcript'][:7000])
                analysis = get_grok_analysis(prompt)
                
                if not analysis or 'segments' not in analysis:
                    st.warning("AI missed it. Falling back to keyword-based detection.")
                    analysis = rule_based_fallback(st.session_state['working_transcript'])
                
                st.session_state['results'] = analysis

    # 3. Results
    if 'results' in st.session_state:
        st.divider()
        segments = st.session_state['results']['segments']
        st.subheader(f"💎 Found {len(segments)} Segments")

        for i, seg in enumerate(segments):
            with st.expander(f"{seg.get('type', 'Clip')} | {seg.get('title', 'Segment')} ({format_time(seg['start'])} - {format_time(seg['end'])})"):
                c1, c2 = st.columns([3, 2])
                
                with c1:
                    if st.session_state.get('video_id'):
                        embed_url = f"https://www.youtube.com/embed/{st.session_state['video_id']}?start={int(seg['start'])}&end={int(seg['end'])}"
                        st.components.v1.iframe(embed_url, height=350)
                    else:
                        st.info("Provide a YouTube URL in Step 1 to see video previews.")
                
                with c2:
                    st.markdown(f"**Hook:** {seg.get('hook', 'N/A')}")
                    st.markdown(f"**Keywords:** {', '.join(seg.get('keywords', []))}")
                    if 'text' in seg:
                        st.caption(f"Transcript Snippet: {seg['text']}")
                    
                    st.text_input("Embed Link", value=f"https://youtu.be/{st.session_state.get('video_id', 'ID')}?t={int(seg['start'])}", key=f"link_{i}")

if __name__ == "__main__":
    main()
