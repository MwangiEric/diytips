#!/usr/bin/env python3
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import re
import json
import groq

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
    'prompts': {
        'segment_analysis': """Analyze this insurance transcript for high-value social media segments. 

INSTRUCTIONS:
- Identify every distinct valuable thought (Micro-hooks and Long-form explanations).
- Segments can overlap or be nested (e.g., a 20s hook inside a 2-minute explanation).
- Focus on emotional triggers, policy benefits, and clear calls to action.

RETURN JSON FORMAT ONLY:
{{
  "segments": [
    {{
      "title": "Descriptive Title", 
      "start": seconds, 
      "end": seconds, 
      "hook": "Social Media Hook/Rationale", 
      "type": "Short/Long"
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

def parse_raw_text_to_dict(text):
    """Maps timestamps to text for retrieval"""
    mapping = []
    lines = text.strip().split('\n')
    for line in lines:
        time_match = re.search(r'\[(\d+):(\d+):(\d+)\]', line)
        if time_match:
            h, m, s = map(int, time_match.groups())
            total_seconds = h * 3600 + m * 60 + s
            content = line[time_match.end():].strip()
            mapping.append({'start': total_seconds, 'text': content})
    return mapping

def get_text_for_range(mapping, start_s, end_s):
    """Grabs all transcript lines that fall within the AI's chosen time window"""
    relevant_text = [item['text'] for item in mapping if start_s <= item['start'] < end_s]
    return " ".join(relevant_text) if relevant_text else "No transcript text found for this window."

def get_grok_analysis(prompt):
    try:
        api_key = st.secrets.get("groq_key")
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

# ----------------------------
# STREAMLIT UI
# ----------------------------

def main():
    st.set_page_config(page_title="AI Insurance Miner", layout="wide")
    st.title("🎯 AI Insurance Content Miner")

    # 1. Inputs
    col_a, col_b = st.columns(2)
    with col_a:
        video_url = st.text_input("YouTube URL (for video preview)")
        v_id = extract_video_id(video_url)
        if v_id: st.session_state['video_id'] = v_id

    with col_b:
        transcript_input = st.text_area("Paste Transcript with [HH:MM:SS]", height=150)
        if st.button("Auto-Fetch YT Transcript") and v_id:
            try:
                data = YouTubeTranscriptApi.get_transcript(v_id, proxies=CONFIG['video']['proxy_config'])
                formatted = ""
                for e in data:
                    s = int(e['start'])
                    ts = f"[{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}]"
                    formatted += f"{ts} {e['text']}\n"
                transcript_input = formatted
                st.session_state['working_transcript'] = formatted
                st.rerun()
            except: st.error("Could not fetch. Please paste manually.")

    if transcript_input:
        st.session_state['working_transcript'] = transcript_input

    # 2. Action
    if 'working_transcript' in st.session_state:
        if st.button("🚀 Mine High-Value Clips", type="primary"):
            with st.spinner("AI is analyzing text and mapping segments..."):
                prompt = CONFIG['prompts']['segment_analysis'].format(transcript=st.session_state['working_transcript'][:8000])
                analysis = get_grok_analysis(prompt)
                if analysis: st.session_state['results'] = analysis

    # 3. Results
    if 'results' in st.session_state:
        st.divider()
        segments = st.session_state['results']['segments']
        mapping = parse_raw_text_to_dict(st.session_state['working_transcript'])

        for i, seg in enumerate(segments):
            # Automated text retrieval
            full_text = get_text_for_range(mapping, seg['start'], seg['end'])
            
            with st.expander(f"🎬 {seg['title']} ({int(seg['start'])}s - {int(seg['end'])}s)"):
                st.markdown("### 📖 Full Segment Script")
                st.info(full_text)
                
                c1, c2 = st.columns([3, 1])
                with c1:
                    if st.session_state.get('video_id'):
                        url = f"https://www.youtube.com/embed/{st.session_state['video_id']}?start={int(seg['start'])}&end={int(seg['end'])}&rel=0"
                        st.components.v1.iframe(url, height=400)
                
                with c2:
                    st.write(f"🎯 **Hook/Strategy:** {seg.get('hook')}")
                    st.write(f"⏱️ **Duration:** {int(seg['end'] - seg['start'])}s")
                    if st.button("📋 Copy Script", key=f"copy_{i}"):
                        st.write("Script copied to clipboard (simulated)")
                        st.session_state['clipboard'] = full_text

if __name__ == "__main__":
    main()
