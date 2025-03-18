import streamlit as st
import yt_dlp
from moviepy.editor import VideoFileClip
from faster_whisper import WhisperModel
import os

# Download YouTube video using yt-dlp
def download_youtube_video(url, output_path='video.mp4'):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        'outtmpl': output_path,
        'merge_output_format': 'mp4'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path

# Extract audio from video
def extract_audio(video_path, audio_output_path='audio.wav'):
    with VideoFileClip(video_path) as video:
        audio = video.audio
        audio.write_audiofile(audio_output_path, codec='pcm_s16le')
    return audio_output_path

# Transcribe audio using Faster-Whisper
def transcribe_audio(audio_path):
    model = WhisperModel("base", compute_type="int8", device="cpu")
    segments, _ = model.transcribe(audio_path)
    return [(segment.text, segment.start, segment.end) for segment in segments]

# Get highlight section based on keyword
def get_highlight_section(transcriptions, keyword='important'):
    for text, start, end in transcriptions:
        if keyword.lower() in text.lower():
            return start, end
    return None, None

# Crop video based on highlight timestamps
def crop_video(input_video_path, output_video_path, start_time, end_time):
    with VideoFileClip(input_video_path) as video:
        subclip = video.subclip(start_time, end_time)
        subclip.write_videofile(output_video_path, codec='libx264', audio_codec='aac')
    return output_video_path

# Create YouTube Shorts (9:16 aspect ratio) with increased duration
def create_youtube_short(input_video_path, output_video_path, start_time, end_time):
    max_duration = 60  # Increase YouTube Shorts duration to 60 seconds
    if end_time - start_time > max_duration:
        end_time = start_time + max_duration

    with VideoFileClip(input_video_path) as video:
        subclip = video.subclip(start_time, end_time)
        width, height = video.size

        # Adjust for 9:16 aspect ratio
        new_width = int(height * 9 / 16)
        x_center = width / 2
        x1, x2 = int(x_center - new_width / 2), int(x_center + new_width / 2)

        cropped_video = subclip.crop(x1=x1, x2=x2)
        cropped_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')
    return output_video_path

# Streamlit UI
def main():
    st.title("YouTube Video Processor")
    url = st.text_input("Enter YouTube video URL:")
    keyword = st.text_input("Enter keyword to search for highlights:", "important")

    if st.button("Process Video"):
        if url:
            with st.spinner("Downloading video..."):
                video_path = download_youtube_video(url)
                st.success(f"Downloaded video: {video_path}")

            with st.spinner("Extracting audio..."):
                audio_path = extract_audio(video_path)
                st.success(f"Extracted audio: {audio_path}")

            with st.spinner("Transcribing audio..."):
                transcriptions = transcribe_audio(audio_path)
                if transcriptions:
                    st.success("Transcription completed.")
                    start_time, end_time = get_highlight_section(transcriptions, keyword)
                    
                    if start_time is not None and end_time is not None:
                        st.info(f"Highlight section: Start - {start_time}s, End - {end_time}s")

                        # Create Highlight Video
                        highlight_video_path = "highlight.mp4"
                        with st.spinner("Creating highlight video..."):
                            highlight_video_path = crop_video(video_path, highlight_video_path, start_time, end_time)
                            st.success(f"Highlight video created: {highlight_video_path}")
                            st.video(highlight_video_path)

                        # Create YouTube Short
                        youtube_short_path = "youtube_short.mp4"
                        with st.spinner("Creating YouTube Short..."):
                            youtube_short_path = create_youtube_short(video_path, youtube_short_path, start_time, end_time)
                            st.success(f"YouTube Short created: {youtube_short_path}")
                            st.video(youtube_short_path)
                    else:
                        st.warning("No significant highlight found.")
                else:
                    st.error("Transcription failed.")
        else:
            st.error("Please enter a valid YouTube URL.")

if __name__ == "__main__":
    main()
