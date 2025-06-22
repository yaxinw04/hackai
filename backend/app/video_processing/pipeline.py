"""
Main video processing pipeline that integrates all components.
"""

import os
import sys
import tempfile
import shutil
import time
from typing import List, Dict
from pathlib import Path

# CRITICAL: Set FFmpeg environment variables BEFORE any video library imports
# This prevents Santa restrictions on bundled FFmpeg binaries
system_ffmpeg = shutil.which('ffmpeg')
if system_ffmpeg:
    os.environ['USE_SYSTEM_FFMPEG'] = '1'
    os.environ['IMAGEIO_FFMPEG_EXE'] = system_ffmpeg
    print(f"🎬 Pre-import FFmpeg config: {system_ffmpeg}")
elif os.path.exists('/opt/homebrew/bin/ffmpeg'):
    os.environ['USE_SYSTEM_FFMPEG'] = '1'
    os.environ['IMAGEIO_FFMPEG_EXE'] = '/opt/homebrew/bin/ffmpeg'
    print(f"🎬 Pre-import FFmpeg config: /opt/homebrew/bin/ffmpeg")
elif os.path.exists('/usr/local/bin/ffmpeg'):
    os.environ['USE_SYSTEM_FFMPEG'] = '1'
    os.environ['IMAGEIO_FFMPEG_EXE'] = '/usr/local/bin/ffmpeg'
    print(f"🎬 Pre-import FFmpeg config: /usr/local/bin/ffmpeg")

from .transcribe import transcribe_video
from .segments import detect_segments, score_segments
from .captions import generate_captions

# Try to import video processing dependencies
try:
    # MoviePy 2.x uses different import structure
    try:
        from moviepy import VideoFileClip
        import moviepy.config as moviepy_config
    except ImportError:
        # Fallback for older MoviePy versions
        from moviepy.editor import VideoFileClip
        import moviepy.config as moviepy_config
    
    # Configure MoviePy to use system FFmpeg instead of bundled version
    # This avoids Shopify Santa restrictions on bundled binaries
    
    # Check if forced to use system FFmpeg via environment variable
    force_system_ffmpeg = os.getenv('USE_SYSTEM_FFMPEG', '').lower() in ('1', 'true', 'yes')
    
    # Try to find system FFmpeg installation
    system_ffmpeg = shutil.which('ffmpeg')
    
    if system_ffmpeg and (force_system_ffmpeg or not os.getenv('MOVIEPY_BUNDLED_FFMPEG')):
        print(f"🎬 Using system FFmpeg: {system_ffmpeg}")
        moviepy_config.FFMPEG_BINARY = system_ffmpeg
        # Also set environment variable to prevent imageio_ffmpeg from downloading
        os.environ['IMAGEIO_FFMPEG_EXE'] = system_ffmpeg
    else:
        # Try common Homebrew locations
        homebrew_paths = [
            '/opt/homebrew/bin/ffmpeg',  # Apple Silicon Macs
            '/usr/local/bin/ffmpeg',     # Intel Macs
            '/usr/bin/ffmpeg'            # Linux systems
        ]
        
        for path in homebrew_paths:
            if os.path.exists(path):
                print(f"🎬 Using FFmpeg at: {path}")
                moviepy_config.FFMPEG_BINARY = path
                os.environ['IMAGEIO_FFMPEG_EXE'] = path
                system_ffmpeg = path
                break
    
    if not system_ffmpeg:
        print("⚠️ System FFmpeg not found. MoviePy will use bundled version (may trigger Santa)")
        print("💡 Install FFmpeg with: brew install ffmpeg")
        print("💡 Or set USE_SYSTEM_FFMPEG=1 environment variable")
    
    MOVIEPY_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    print("🎭 MoviePy not available:", e)
    if "Santa" in str(e) or "not approved" in str(e):
        print("🚫 Shopify Santa detected! FFmpeg binary blocked.")
        print("💡 Solutions:")
        print("   1. Install system FFmpeg: brew install ffmpeg")
        print("   2. Set environment variable: export USE_SYSTEM_FFMPEG=1")
        print("   3. Contact IT about approving FFmpeg binary")
    MOVIEPY_AVAILABLE = False

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False


def download_youtube_video(url: str, output_path: str) -> str:
    """Download a YouTube video and return the path to the downloaded file."""
    if not YT_DLP_AVAILABLE:
        # Create a mock video file for demo
        print("🎭 Creating mock video file for demo...")
        mock_path = output_path.replace('%(ext)s', 'mp4')
        with open(mock_path, 'w') as f:
            f.write(f"Mock video file for URL: {url}\n")
            f.write("This is a demo file. Install yt-dlp for real video downloads.\n")
        return mock_path
    
    # Enhanced yt-dlp options to bypass bot detection
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_path,
        'noplaylist': True,
        'sleep_interval': 1,  # Add delays between requests
        'max_sleep_interval': 3,
        'extract_flat': False,
        'ignoreerrors': False,
        'no_warnings': False,
        'writesubtitles': False,
        'writeautomaticsub': False,
        # Add user agent to appear less bot-like
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        # Retry options
        'retries': 3,
        'file_access_retries': 3,
        'fragment_retries': 3,
        # Network options
        'socket_timeout': 30,
        # Try to use embedded player
        'youtube_include_dash_manifest': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        error_msg = str(e)
        print(f"❌ YouTube download failed: {error_msg}")
        
        # Check if it's a bot detection error
        if "Sign in to confirm" in error_msg or "not a bot" in error_msg:
            print("🤖 YouTube bot detection triggered")
            print("💡 This is a common issue with YouTube's anti-bot measures")
            print("🎭 Falling back to demo mode...")
            raise Exception(f"YouTube bot detection: {error_msg}")
        else:
            # For other errors, also fall back to demo
            print(f"🎭 Falling back to demo mode due to: {error_msg}")
            raise Exception(f"YouTube download error: {error_msg}")


def create_video_clip(source_video: str, start_time: float, end_time: float, output_path: str) -> str:
    """Create a video clip from the source video between start and end times."""
    if not MOVIEPY_AVAILABLE:
        # Create a mock clip file for demo
        print(f"🎭 Creating mock clip file: {os.path.basename(output_path)}")
        with open(output_path.replace('.mp4', '_info.txt'), 'w') as f:
            f.write(f"MOCK VIDEO CLIP\n")
            f.write(f"================\n\n")
            f.write(f"Source: {source_video}\n")
            f.write(f"Start Time: {start_time:.2f}s\n")
            f.write(f"End Time: {end_time:.2f}s\n")
            f.write(f"Duration: {end_time - start_time:.2f}s\n\n")
            f.write("This is a demo file. Install moviepy and ffmpeg for real video clips.\n")
            f.write("Run: pip install moviepy\n")
            f.write("Install ffmpeg: brew install ffmpeg (Mac) or apt install ffmpeg (Ubuntu)\n")
        return output_path.replace('.mp4', '_info.txt')
    
    with VideoFileClip(source_video) as video:
        # MoviePy 2.x uses 'subclipped' instead of 'subclip'
        if hasattr(video, 'subclipped'):
            clip = video.subclipped(start_time, end_time)
        else:
            # Fallback for older MoviePy versions
            clip = video.subclip(start_time, end_time)
        clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
    
    return output_path


def create_demo_clips(job_id: str, url: str, prompt: str, output_dir: str) -> List[str]:
    """Create demo clips with realistic metadata when dependencies aren't available."""
    
    print(f"🎭 Creating demo clips for: {url}")
    time.sleep(2)  # Simulate processing time
    
    # Create organized output directory structure
    job_output_dir = os.path.join(output_dir, job_id)
    clips_dir = os.path.join(job_output_dir, "clips")
    os.makedirs(clips_dir, exist_ok=True)
    
    # Parse prompt for number of clips
    top_k = 3  # default
    if "clip" in prompt.lower():
        words = prompt.lower().split()
        for i, word in enumerate(words):
            if word.isdigit() and i > 0 and words[i-1] in ["create", "make", "generate"]:
                top_k = int(word)
                break
    
    demo_clips = [
        {
            "title": "Opening Hook",
            "start": 15.0,
            "end": 35.0,
            "text": "Welcome to today's video! This opening will grab your attention with an incredible insight.",
            "caption": "This will blow your mind! 🤯",
            "hashtags": ["#viral", "#mindblown", "#mustsee"]
        },
        {
            "title": "Key Insight",
            "start": 145.0,
            "end": 175.0,
            "text": "Here's the main point that everyone needs to understand. This changes everything!",
            "caption": "Game changer right here! 🔥",
            "hashtags": ["#gamechange", "#amazing", "#viral"]
        },
        {
            "title": "Viral Moment",
            "start": 280.0,
            "end": 320.0,
            "text": "Wait until you see this incredible result! You won't believe what happens next.",
            "caption": "You won't believe this! 😱",
            "hashtags": ["#shocking", "#unbelievable", "#epic"]
        },
        {
            "title": "Pro Tip",
            "start": 420.0,
            "end": 450.0,
            "text": "Here's the secret technique that most people don't know about. This is pure gold!",
            "caption": "This is pure gold! ✨",
            "hashtags": ["#protip", "#secret", "#viral"]
        },
        {
            "title": "Perfect Ending",
            "start": 580.0,
            "end": 610.0,
            "text": "Thanks for watching! Make sure to try this yourself and let me know how it goes.",
            "caption": "Try this yourself! 🚀",
            "hashtags": ["#tryit", "#results", "#viral"]
        }
    ]
    
    # Select the requested number of clips
    selected_clips = demo_clips[:top_k]
    output_paths = []
    clip_metadata = []
    
    for i, clip in enumerate(selected_clips):
        # Create demo clip info file
        clip_filename = f"clip_{i+1}_demo.txt"
        clip_path = os.path.join(clips_dir, clip_filename)
        
        with open(clip_path, 'w') as f:
            f.write(f"🎬 DEMO CLIP {i+1}: {clip['title']}\n")
            f.write(f"{'='*50}\n\n")
            f.write(f"📍 Time Range: {clip['start']:.1f}s - {clip['end']:.1f}s\n")
            f.write(f"⏱️ Duration: {clip['end'] - clip['start']:.1f} seconds\n\n")
            f.write(f"📝 Content:\n{clip['text']}\n\n")
            f.write(f"📱 Caption: {clip['caption']}\n")
            f.write(f"🏷️ Hashtags: {' '.join(clip['hashtags'])}\n\n")
            f.write(f"🎯 Original URL: {url}\n")
            f.write(f"💭 User Prompt: {prompt}\n\n")
            f.write("ℹ️ This is a demo file showing what would be created.\n")
            f.write("Install video dependencies for actual MP4 clips:\n")
            f.write("• pip install yt-dlp moviepy openai-whisper\n")
            f.write("• brew install ffmpeg (macOS) or apt install ffmpeg (Linux)\n")
        
        # Store clip metadata (for demo mode)
        clip_info = {
            "id": i + 1,
            "filename": clip_filename,
            "title": clip['title'],
            "start_time": clip['start'],
            "end_time": clip['end'],
            "duration": clip['end'] - clip['start'],
            "startTime": f"{int(clip['start']//60):02d}:{int(clip['start']%60):02d}",
            "endTime": f"{int(clip['end']//60):02d}:{int(clip['end']%60):02d}",
            "text": clip['text'],
            "caption": clip['caption'],
            "hashtags": clip['hashtags'],
            "path": f"/clips/{job_id}/clips/{clip_filename}",
            "url_path": f"/clips/{job_id}/clips/{clip_filename}",
            "is_demo": True
        }
        clip_metadata.append(clip_info)
        
        output_paths.append(clip_path)
        print(f"✨ Created demo clip: {clip['title']}")
    
    # Save metadata to JSON file
    import json
    metadata_path = os.path.join(job_output_dir, "metadata.json")
    job_metadata = {
        "job_id": job_id,
        "url": url,
        "prompt": prompt,
        "total_clips": len(clip_metadata),
        "clips": clip_metadata,
        "created_at": str(time.time()),
        "is_demo": True
    }
    with open(metadata_path, 'w') as f:
        json.dump(job_metadata, f, indent=2)
    print(f"📝 Saved demo metadata to: {metadata_path}")
    
    return output_paths


def run_processing_pipeline(job_id: str, url: str, prompt: str, output_dir: str) -> List[str]:
    """
    Complete video processing pipeline that:
    1. Downloads the YouTube video
    2. Transcribes it
    3. Detects and scores segments
    4. Generates captions
    5. Creates video clips
    
    Returns a list of paths to the generated video clips or demo files.
    """
    print(f"🚀 Starting processing pipeline for job {job_id}")
    print(f"📹 URL: {url}")
    print(f"💭 Prompt: {prompt}")
    
    # Check if we have all dependencies for full processing
    has_full_deps = YT_DLP_AVAILABLE and MOVIEPY_AVAILABLE

    print("YT_DLP_AVAILABLE", YT_DLP_AVAILABLE  )
    print("MOVIEPY_AVAILABLE", MOVIEPY_AVAILABLE)
    
    if not has_full_deps:
        print("⚠️ Missing video dependencies, creating demo clips...")
        return create_demo_clips(job_id, url, prompt, output_dir)
    
    output_clips = []
    temp_dir = None
    
    # Create organized output directory structure
    job_output_dir = os.path.join(output_dir, job_id)
    clips_dir = os.path.join(job_output_dir, "clips")
    os.makedirs(clips_dir, exist_ok=True)
    
    try:
        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        print(f"📁 Working directory: {temp_dir}")
        print(f"📁 Job output directory: {job_output_dir}")
        
        # Step 1: Download YouTube video
        print(f"⬇️ Downloading video from {url}")
        video_filename = f"{job_id}_video.%(ext)s"
        video_path = os.path.join(temp_dir, video_filename)
        downloaded_video = download_youtube_video(url, video_path)
        
        # Find the actual downloaded file (yt-dlp might change the extension)
        downloaded_files = [f for f in os.listdir(temp_dir) if f.startswith(f"{job_id}_video")]
        if not downloaded_files:
            raise Exception("Failed to download video")
        
        actual_video_path = os.path.join(temp_dir, downloaded_files[0])
        print(f"✅ Video downloaded: {actual_video_path}")
        
        # Step 2: Transcribe video
        print(f"🎙️ Transcribing video...")
        transcript_segments = transcribe_video(actual_video_path)
        print(f"✅ Transcription complete: {len(transcript_segments)} segments")
        
        # Step 3: Detect and score segments
        print(f"🎯 Detecting optimal segments...")
        chunks = detect_segments(actual_video_path, transcript_segments)
        print(f"✅ Found {len(chunks)} potential chunks")
        
        # Parse the prompt to determine how many clips to create
        top_k = 3  # default
        if "clip" in prompt.lower():
            words = prompt.lower().split()
            for i, word in enumerate(words):
                if word.isdigit() and i > 0 and words[i-1] in ["create", "make", "generate"]:
                    top_k = int(word)
                    break
        
        top_chunks = score_segments(chunks, top_k=top_k)
        print(f"🏆 Selected top {len(top_chunks)} chunks")
        
        # Step 4: Generate captions
        print(f"✨ Generating captions and hashtags...")
        try:
            captioned_chunks = generate_captions(top_chunks)
            print(f"✅ Captions generated")
        except Exception as e:
            print(f"⚠️ Caption generation failed: {e}")
            captioned_chunks = top_chunks
        
        # Step 5: Create video clips
        print(f"🎬 Creating video clips...")
        clip_metadata = []
        
        for i, chunk in enumerate(captioned_chunks):
            clip_filename = f"clip_{i+1}.mp4"
            clip_path = os.path.join(clips_dir, clip_filename)
            
            try:
                created_clip = create_video_clip(
                    actual_video_path,
                    chunk['start'],
                    chunk['end'],
                    clip_path
                )
                
                # Store clip metadata
                clip_info = {
                    "id": i + 1,
                    "filename": clip_filename,
                    "title": chunk.get('title', f'Clip {i+1}'),
                    "start_time": chunk['start'],
                    "end_time": chunk['end'],
                    "duration": chunk['end'] - chunk['start'],
                    "text": chunk['text'],
                    "caption": chunk.get('caption', ''),
                    "hashtags": chunk.get('hashtags', []),
                    "url_path": f"/clips/{job_id}/clips/{clip_filename}"
                }
                clip_metadata.append(clip_info)
                
                output_clips.append(created_clip)
                print(f"✅ Created clip {i+1}: {clip_filename}")
            except Exception as e:
                print(f"❌ Failed to create clip {i+1}: {e}")
                # Create info file instead
                info_path = os.path.join(clips_dir, f"clip_{i+1}_error.txt")
                with open(info_path, 'w') as f:
                    f.write(f"Clip {i+1} Info:\n")
                    f.write(f"Title: {chunk.get('title', 'Untitled')}\n")
                    f.write(f"Start: {chunk['start']:.2f}s\n")
                    f.write(f"End: {chunk['end']:.2f}s\n")
                    f.write(f"Duration: {chunk['end'] - chunk['start']:.2f}s\n")
                    f.write(f"Text: {chunk['text']}\n")
                    if 'caption' in chunk:
                        f.write(f"Caption: {chunk['caption']}\n")
                    if 'hashtags' in chunk:
                        f.write(f"Hashtags: {' '.join(chunk['hashtags'])}\n")
                    f.write(f"\nError: {e}\n")
        
        # Save metadata to JSON file
        if clip_metadata:
            metadata_path = os.path.join(job_output_dir, "metadata.json")
            import json
            job_metadata = {
                "job_id": job_id,
                "url": url,
                "prompt": prompt,
                "total_clips": len(clip_metadata),
                "clips": clip_metadata,
                "created_at": str(time.time())
            }
            with open(metadata_path, 'w') as f:
                json.dump(job_metadata, f, indent=2)
            print(f"📝 Saved metadata to: {metadata_path}")
        
        print(f"🎉 Pipeline complete: {len(output_clips)} clips created")
        return output_clips
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        print("🎭 Falling back to demo mode...")
        return create_demo_clips(job_id, url, prompt, output_dir)
    
    finally:
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"🧹 Cleaned up temporary files")
            except Exception as e:
                print(f"⚠️ Failed to cleanup temp directory: {e}")


if __name__ == "__main__":
    # Test the pipeline
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    test_prompt = "Create 2 engaging clips"
    test_output_dir = "test_output"
    
    os.makedirs(test_output_dir, exist_ok=True)
    
    try:
        clips = run_processing_pipeline("test", test_url, test_prompt, test_output_dir)
        print(f"\n🎉 Success! Created {len(clips)} clips:")
        for clip in clips:
            print(f"  📁 {clip}")
    except Exception as e:
        print(f"\n❌ Error: {e}") 