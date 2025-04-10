import streamlit as st
import os
import tempfile
import time
from pathlib import Path
import base64

from utils import (
    generate_voiceover_text,
    generate_voiceover_audio,
    merge_video_with_audio,
    get_video_duration
)

# Set page configuration
st.set_page_config(
    page_title="Ryan's Social Media Maker",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 500;
        color: #333;
        margin-bottom: 0.5rem;
    }
    .info-text {
        font-size: 1rem;
        color: #555;
    }
    .success-box {
        padding: 1rem;
        background-color: #E8F5E9;
        border-left: 5px solid #4CAF50;
        margin-bottom: 1rem;
    }
    .warning-box {
        padding: 1rem;
        background-color: #FFF8E1;
        border-left: 5px solid #FFC107;
        margin-bottom: 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    /* Floating video style */
    div.stVideo {
        max-width: 200px !important;
        margin-left: 0;
        margin-right: auto;
    }
    div.stVideo > div {
        border-radius: 8px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        overflow: hidden;
        background-color: #f8f9fa;
        border: 1px solid #e9e9e9;
    }
</style>
""", unsafe_allow_html=True)

# Create a function to generate a download link
def get_download_link(file_path, link_text):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:video/mp4;base64,{b64}" download="{os.path.basename(file_path)}">{link_text}</a>'
    return href

# Initialize session state for keeping track of files and processing state
if 'uploaded_video_path' not in st.session_state:
    st.session_state.uploaded_video_path = None
if 'voiceover_text' not in st.session_state:
    st.session_state.voiceover_text = ""
if 'audio_path' not in st.session_state:
    st.session_state.audio_path = None
if 'merged_video_path' not in st.session_state:
    st.session_state.merged_video_path = None
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
if 'video_duration' not in st.session_state:
    st.session_state.video_duration = 0

# App header
st.markdown('<div class="main-header">Ryan\'s Social Media Maker</div>', unsafe_allow_html=True)
st.markdown('<div class="info-text">Upload videos and generate AI voiceovers with customizable voices and volume controls.</div>', unsafe_allow_html=True)

# Create tabs for workflow steps
tab1, tab2, tab3 = st.tabs(["📤 Upload & Generate", "🔊 Voice & Audio Settings", "🎬 Preview & Download"])

with tab1:
    st.markdown('<div class="sub-header">Step 1: Upload Video</div>', unsafe_allow_html=True)
    
    # Video upload section
    uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "mov", "avi", "webm"])
    
    if uploaded_file is not None:
        # Save the uploaded file to a temporary location
        temp_video_path = os.path.join(st.session_state.temp_dir, uploaded_file.name)
        with open(temp_video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Update session state
        st.session_state.uploaded_video_path = temp_video_path
        try:
            st.session_state.video_duration = get_video_duration(temp_video_path)
            st.success(f"Video uploaded successfully! Duration: {st.session_state.video_duration:.2f} seconds")
        except Exception as e:
            st.error(f"Error processing video: {str(e)}")
        
        # Display the uploaded video as a small floating box
        col1, col2, col3 = st.columns([1, 4, 4])
        with col1:
            st.video(temp_video_path, start_time=0)
    
    # Instructions and text generation section
    st.markdown('<div class="sub-header">Step 2: Generate Voiceover Text</div>', unsafe_allow_html=True)
    
    instructions = st.text_area(
        "Provide instructions for the voiceover style and content",
        placeholder="Example: Create a professional, enthusiastic voiceover that explains what's happening in the video. Focus on the main actions and highlight key moments. Use a conversational tone.",
        height=150
    )
    
    if st.button("Generate Voiceover Text", disabled=st.session_state.uploaded_video_path is None):
        if not instructions:
            st.warning("Please provide some instructions for the voiceover.")
        else:
            with st.spinner("Analyzing video and generating voiceover text..."):
                try:
                    # Generate voiceover text
                    st.session_state.voiceover_text = generate_voiceover_text(
                        st.session_state.uploaded_video_path, 
                        instructions
                    )
                    st.success("Voiceover text generated successfully!")
                except Exception as e:
                    st.error(f"Error generating voiceover text: {str(e)}")
    
    # Display and allow editing of the generated text
    if st.session_state.voiceover_text:
        st.markdown('<div class="sub-header">Review and Edit Voiceover Text</div>', unsafe_allow_html=True)
        edited_text = st.text_area(
            "Edit the generated voiceover text as needed",
            st.session_state.voiceover_text,
            height=250
        )
        st.session_state.voiceover_text = edited_text
        
        # Calculate word count and estimated duration
        word_count = len(edited_text.split())
        est_duration = word_count / (200/60)  # 200 words per minute
        
        st.markdown(f"<div class='info-text'>Word count: {word_count} | Estimated duration: {est_duration:.2f} seconds</div>", unsafe_allow_html=True)
        
        if st.session_state.video_duration > 0 and est_duration > st.session_state.video_duration:
            st.markdown(
                f"<div class='warning-box'>⚠️ The estimated voiceover duration ({est_duration:.2f}s) is longer than the video ({st.session_state.video_duration:.2f}s). Consider shortening the text.</div>", 
                unsafe_allow_html=True
            )

with tab2:
    st.markdown('<div class="sub-header">Step 3: Voice and Audio Settings</div>', unsafe_allow_html=True)
    
    # Voice selection dropdown
    voice_options = [
        "nova", "alloy", "ash", "ballad", "coral", 
        "echo", "fable", "onyx", "sage", "shimmer"
    ]
    
    selected_voice = st.selectbox(
        "Select AI Voice",
        voice_options,
        index=voice_options.index("nova")
    )
    
    # Speech rate slider
    speech_speed = st.slider(
        "Speech Speed",
        min_value=0.5,
        max_value=1.5,
        value=1.0,
        step=0.1,
        help="Adjust the speaking rate of the AI voice"
    )
    
    # Volume control sliders
    col1, col2 = st.columns(2)
    
    with col1:
        video_volume = st.slider(
            "Original Video Volume",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Set to 0 to mute the original audio"
        )
    
    with col2:
        audio_volume = st.slider(
            "Voiceover Volume",
            min_value=0.1,
            max_value=1.5,
            value=1.0,
            step=0.1
        )
    
    # Generate audio button
    if st.button("Generate Voiceover Audio", disabled=not st.session_state.voiceover_text):
        with st.spinner("Converting text to speech..."):
            try:
                # Generate a unique filename for the audio
                audio_filename = f"voiceover_{int(time.time())}.mp3"
                audio_path = os.path.join(st.session_state.temp_dir, audio_filename)
                
                # Generate the voiceover audio
                success = generate_voiceover_audio(
                    st.session_state.voiceover_text,
                    audio_path,
                    voice_name=selected_voice,
                    speed=speech_speed
                )
                
                if success:
                    st.session_state.audio_path = audio_path
                    st.success("Voiceover audio generated successfully!")
                    
                    # Display audio player
                    st.audio(audio_path)
                else:
                    st.error("Failed to generate voiceover audio.")
            except Exception as e:
                st.error(f"Error generating audio: {str(e)}")
    
    # Merge audio with video button
    if st.button("Merge Audio with Video", disabled=st.session_state.audio_path is None):
        with st.spinner("Merging audio with video... This may take a moment."):
            try:
                # Generate a unique filename for the merged video
                merged_filename = f"merged_video_{int(time.time())}.mp4"
                merged_path = os.path.join(st.session_state.temp_dir, merged_filename)
                
                # Merge the video with the audio
                merged_path = merge_video_with_audio(
                    st.session_state.uploaded_video_path,
                    st.session_state.audio_path,
                    merged_path,
                    video_volume=video_volume,
                    audio_volume=audio_volume
                )
                
                st.session_state.merged_video_path = merged_path
                st.success("Video and audio merged successfully!")
            except Exception as e:
                st.error(f"Error merging video and audio: {str(e)}")

with tab3:
    st.markdown('<div class="sub-header">Step 4: Preview and Download</div>', unsafe_allow_html=True)
    
    # Create columns for the original and processed videos
    original_col, processed_col = st.columns(2)
    
    with original_col:
        st.markdown("**Original Video**")
        if st.session_state.uploaded_video_path:
            col1, col2, col3 = st.columns([1, 4, 4])
            with col1:
                st.video(st.session_state.uploaded_video_path, start_time=0)
    
    with processed_col:
        st.markdown("**Video with Voiceover**")
        if st.session_state.merged_video_path:
            col1, col2, col3 = st.columns([1, 4, 4])
            with col1:
                st.video(st.session_state.merged_video_path, start_time=0)
            
            # Download button for the processed video
            st.markdown(
                get_download_link(
                    st.session_state.merged_video_path, 
                    "Download Video with Voiceover"
                ),
                unsafe_allow_html=True
            )
        else:
            st.info("Complete the previous steps to generate and view your video with voiceover here.")

# Sidebar with instructions and information
with st.sidebar:
    st.markdown("### How to Use Ryan's Social Media Maker")
    st.markdown("""
    1. **Upload your video** in the first tab
    2. **Provide instructions** for the AI to generate voiceover text
    3. **Review and edit** the generated text if needed
    4. **Select voice and audio settings** in the second tab
    5. **Generate the voiceover** audio from your text
    6. **Adjust volume levels** for both original audio and voiceover
    7. **Merge the audio with your video**
    8. **Preview and download** your finished video in the third tab
    """)
    
    st.markdown("### Available Voices")
    st.markdown("""
    - **Nova** - Default balanced voice
    - **Alloy** - Versatile neutral voice
    - **Ash** - Clear and direct
    - **Ballad** - Melodic, emotive voice
    - **Coral** - Warm and friendly
    - **Echo** - Deep and authoritative
    - **Fable** - Narrative storytelling
    - **Onyx** - Professional and confident
    - **Sage** - Thoughtful and informative
    - **Shimmer** - Bright and enthusiastic
    """)
    
    st.markdown("### Tips")
    st.markdown("""
    - Keep voiceover text concise for better results
    - Adjust speech speed for timing with video content
    - Lower original video volume to 0.3-0.4 for clear voiceover
    - For background music, keep voiceover volume higher (1.0-1.2)
    """)
    
    # Add a footer with version info
    st.markdown("---")
    st.markdown("Ryan's Social Media Maker v1.0")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888;'>Ryan's Social Media Maker | Powered by OpenAI</div>", 
    unsafe_allow_html=True
)

# Cleanup function for removing temporary files when the app is closed
def cleanup():
    if hasattr(st.session_state, 'temp_dir') and os.path.exists(st.session_state.temp_dir):
        import shutil
        try:
            shutil.rmtree(st.session_state.temp_dir)
        except Exception as e:
            print(f"Error cleaning up temporary files: {str(e)}")

# Register the cleanup function to run when the app is closed
import atexit
atexit.register(cleanup)