import os
import uuid
import traceback
import shutil
import json
from typing import Dict, Any
from pathlib import Path

# CRITICAL: Set FFmpeg environment variables BEFORE any video library imports
# This prevents Santa restrictions on bundled FFmpeg binaries in Shopify environments
system_ffmpeg = shutil.which('ffmpeg')
if system_ffmpeg:
    # Set all possible FFmpeg environment variables to force system usage
    os.environ['USE_SYSTEM_FFMPEG'] = '1'
    os.environ['IMAGEIO_FFMPEG_EXE'] = system_ffmpeg
    os.environ['FFMPEG_BINARY'] = system_ffmpeg
    os.environ['MOVIEPY_FFMPEG'] = system_ffmpeg
    print(f"🎬 Main app FFmpeg config: {system_ffmpeg}")
elif os.path.exists('/opt/homebrew/bin/ffmpeg'):
    ffmpeg_path = '/opt/homebrew/bin/ffmpeg'
    os.environ['USE_SYSTEM_FFMPEG'] = '1'
    os.environ['IMAGEIO_FFMPEG_EXE'] = ffmpeg_path
    os.environ['FFMPEG_BINARY'] = ffmpeg_path
    os.environ['MOVIEPY_FFMPEG'] = ffmpeg_path
    print(f"🎬 Main app FFmpeg config: {ffmpeg_path}")
elif os.path.exists('/usr/local/bin/ffmpeg'):
    ffmpeg_path = '/usr/local/bin/ffmpeg'
    os.environ['USE_SYSTEM_FFMPEG'] = '1'
    os.environ['IMAGEIO_FFMPEG_EXE'] = ffmpeg_path
    os.environ['FFMPEG_BINARY'] = ffmpeg_path
    os.environ['MOVIEPY_FFMPEG'] = ffmpeg_path
    print(f"🎬 Main app FFmpeg config: {ffmpeg_path}")
else:
    print("⚠️ System FFmpeg not found - video processing may trigger Santa restrictions")

from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .storage import job_manager, storage_backend
from .schemas import (
    ProcessRequest, ProcessResponse, JobStatusResponse, ClipMetadata,
    FinalizeRequest, FinalizeResponse, EditedClip,
    GenerateCaptionsRequest, GenerateCaptionsResponse, CaptionSegment,
    ApplyCaptionsRequest, ApplyCaptionsResponse, CaptionStyle
)

# Import the video processing pipeline
try:
    from .video_processing import run_processing_pipeline
    VIDEO_PROCESSOR_AVAILABLE = True
    print("✅ Video processing pipeline loaded successfully")
except ImportError as e:
    VIDEO_PROCESSOR_AVAILABLE = False
    print(f"❌ Video processing pipeline not available: {e}")
    print("Check backend/app/video_processing/ module")

# Import caption processing
try:
    from .video_processing.transcribe import transcribe_video
    from .video_processing.caption_burner import apply_captions_to_video
    CAPTION_PROCESSOR_AVAILABLE = True
    print("✅ Caption processing loaded successfully")
except ImportError as e:
    CAPTION_PROCESSOR_AVAILABLE = False
    print(f"❌ Caption processing not available: {e}")

app = FastAPI(
    title="YouTube to Shorts API",
    description="API for converting YouTube videos to short clips",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup local static file serving for clips (only if not using S3)
if not settings.USE_S3:
    output_dir = Path(settings.LOCAL_OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)
    app.mount("/clips", StaticFiles(directory=str(output_dir)), name="clips")
    print(f"📁 Local file serving enabled: {output_dir}")
else:
    print(f"☁️ S3 storage enabled: {settings.S3_BUCKET}")

print(f"🚀 Backend started with {len(job_manager.jobs)} existing jobs")


def format_duration(seconds: float) -> str:
    """Format duration nicely with proper rounding"""
    total_secs = round(seconds * 10) / 10  # Round to 1 decimal place
    mins = int(total_secs // 60)
    remaining_secs = total_secs % 60
    
    if mins > 0:
        # For longer durations, show as MM:SS
        return f"{mins}:{int(remaining_secs):02d}"
    else:
        # For shorter durations, show as seconds with 1 decimal if needed
        return f"{remaining_secs:.0f}s" if remaining_secs % 1 == 0 else f"{remaining_secs:.1f}s"


async def process_video_background(job_id: str, url: str, prompt: str):
    """Background task to process video using the ml_stuff pipeline"""
    try:
        # Update job status to processing
        job_data = job_manager.load_job(job_id)
        if not job_data:
            print(f"❌ Job {job_id} not found")
            return
            
        job_data["status"] = "processing"
        job_data["message"] = "Processing video..."
        job_manager.save_job(job_id, job_data)
        
        if not VIDEO_PROCESSOR_AVAILABLE:
            raise Exception("Video processing pipeline is not available")
        
        print(f"🎬 Starting processing for job {job_id}")
        # Call the ml_stuff processing pipeline
        output_paths = run_processing_pipeline(
            job_id=job_id,
            url=url,
            prompt=prompt,
            output_dir=settings.LOCAL_OUTPUT_DIR
        )
        
        # Load metadata if available, otherwise fall back to paths
        local_job_dir = Path(settings.LOCAL_OUTPUT_DIR) / job_id
        metadata_path = local_job_dir / "metadata.json"
        
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Upload videos to storage and update URLs
            if settings.USE_S3:
                for clip in metadata["clips"]:
                    if "path" in clip and clip["path"].startswith("/clips/"):
                        # Extract local file path
                        local_file_path = Path(settings.LOCAL_OUTPUT_DIR) / clip["path"][7:]  # Remove "/clips/"
                        if local_file_path.exists():
                            filename = local_file_path.name
                            public_url = job_manager.upload_video(str(local_file_path), job_id, filename)
                            clip["path"] = public_url
                            clip["url_path"] = public_url
            
            # Update job status to complete with metadata
            job_data["status"] = "complete"
            job_data["message"] = "Processing completed successfully"
            job_data["results"] = metadata["clips"]
            job_data["metadata"] = metadata
            job_data["is_demo"] = metadata.get("is_demo", False)
            print(f"✅ Job {job_id} completed successfully with {len(metadata['clips'])} clips")
        else:
            # Convert absolute paths to relative URLs for the frontend (fallback)
            results = []
            for path in output_paths:
                if os.path.exists(path):
                    filename = os.path.basename(path)
                    if settings.USE_S3:
                        public_url = job_manager.upload_video(path, job_id, filename)
                        results.append(public_url)
                    else:
                        results.append(f"/clips/{job_id}/{filename}")
            
            # Update job status to complete
            job_data["status"] = "complete"
            job_data["message"] = "Processing completed successfully"
            job_data["results"] = results
            job_data["is_demo"] = True  # Assume demo if no metadata
            print(f"✅ Job {job_id} completed with {len(results)} clips (fallback mode)")
        
        job_manager.save_job(job_id, job_data)
        
    except Exception as e:
        # Update job status to failed
        job_data = job_manager.load_job(job_id)
        if job_data:
            job_data["status"] = "failed"
            job_data["message"] = f"Processing failed: {str(e)}"
            job_data["error"] = traceback.format_exc()
            job_manager.save_job(job_id, job_data)
        print(f"❌ Job {job_id} failed: {e}")
        print(traceback.format_exc())


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "YouTube to Shorts API with Captions",
        "version": "1.0.0",
        "jobs_count": len(jobs),
        "endpoints": {
            "process": "POST /process",
            "status": "GET /status/{job_id}",
            "finalize": "POST /finalize/{job_id}",
            "generate_captions": "POST /captions/generate",
            "apply_captions": "POST /captions/apply",
            "clips": "GET /clips/{filename}",
            "debug": "GET /jobs",
            "health": "GET /health"
        },
        "features": {
            "video_processing": VIDEO_PROCESSOR_AVAILABLE,
            "caption_processing": CAPTION_PROCESSOR_AVAILABLE,
            "youtube_shorts_styling": True,
            "ai_transcription": True
        }
    }


@app.post("/process", response_model=ProcessResponse)
async def process_video(request: ProcessRequest, background_tasks: BackgroundTasks):
    """Start processing a YouTube video into shorts"""
    
    if not VIDEO_PROCESSOR_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Video processing pipeline is not available. Check that video_processing module exists and dependencies are installed."
        )
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    job_data = {
        "status": "pending",
        "message": "Job queued for processing",
        "url": request.url,
        "prompt": request.prompt,
        "results": None,
        "created_at": str(Path().cwd())  # timestamp placeholder
    }
    
    job_manager.save_job(job_id, job_data)
    
    print(f"🆕 Created job {job_id} for URL: {request.url}")
    
    # Add background task
    background_tasks.add_task(
        process_video_background,
        job_id=job_id,
        url=request.url,
        prompt=request.prompt
    )
    
    return ProcessResponse(
        job_id=job_id,
        status="pending",
        message="Job started successfully"
    )


@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of a processing job"""
    
    job = job_manager.load_job(job_id)
    
    if not job:
        print(f"❌ Job {job_id} not found in storage or memory")
        print(f"📊 Available jobs: {list(job_manager.jobs.keys())}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    print(f"📋 Status check for job {job_id}: {job['status']}")
    
    return JobStatusResponse(
        status=job["status"],
        message=job["message"],
        results=job.get("results"),
        is_demo=job.get("is_demo", False),
        metadata=job.get("metadata")
    )


@app.get("/jobs")
async def list_jobs():
    """List all jobs (for debugging)"""
    return {
        "total_jobs": len(job_manager.jobs),
        "storage_type": "S3" if settings.USE_S3 else "Local",
        "storage_location": settings.S3_BUCKET if settings.USE_S3 else settings.LOCAL_OUTPUT_DIR,
        "jobs": {job_id: {
            "status": job["status"], 
            "message": job["message"],
            "url": job.get("url", ""),
            "has_results": job.get("results") is not None,
            "has_finalized": job.get("finalized_results") is not None,
            "created_at": job.get("created_at", "unknown")
        } for job_id, job in job_manager.jobs.items()}
    }


@app.get("/debug/{job_id}")
async def debug_job(job_id: str):
    """Debug a specific job"""
    job = job_manager.load_job(job_id)
    
    # Check if local files exist (even when using S3)
    local_job_dir = Path(settings.LOCAL_OUTPUT_DIR) / job_id
    original_clips_dir = local_job_dir / "original_clips"
    finalized_clips_dir = local_job_dir / "finalized_clips"
    
    return {
        "job_id": job_id,
        "in_storage": job is not None,
        "job_data": job,
        "storage_config": {
            "use_s3": settings.USE_S3,
            "s3_bucket": settings.S3_BUCKET,
            "local_dir": settings.LOCAL_OUTPUT_DIR
        },
        "file_system": {
            "job_dir_exists": local_job_dir.exists(),
            "original_clips_dir_exists": original_clips_dir.exists(),
            "finalized_clips_dir_exists": finalized_clips_dir.exists(),
            "original_clips_count": len(list(original_clips_dir.glob("*.mp4"))) if original_clips_dir.exists() else 0,
            "finalized_clips_count": len(list(finalized_clips_dir.glob("*.mp4"))) if finalized_clips_dir.exists() else 0,
            "job_dir_contents": [f.name for f in local_job_dir.iterdir()] if local_job_dir.exists() else []
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENV,
        "video_processor_available": VIDEO_PROCESSOR_AVAILABLE,
        "caption_processor_available": CAPTION_PROCESSOR_AVAILABLE,
        "total_jobs": len(job_manager.jobs),
        "storage": {
            "type": "S3" if settings.USE_S3 else "Local",
            "bucket": settings.S3_BUCKET if settings.USE_S3 else None,
            "local_dir": settings.LOCAL_OUTPUT_DIR,
            "base_url": settings.base_url
        },
        "ffmpeg_path": os.environ.get('FFMPEG_BINARY', 'not_set'),
        "cors_origins": settings.CORS_ORIGINS
    }


@app.post("/captions/generate", response_model=GenerateCaptionsResponse)
async def generate_captions(request: GenerateCaptionsRequest):
    """Generate captions for a video clip using speech recognition"""
    
    if not CAPTION_PROCESSOR_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Caption processing is not available"
        )
    
    job_id = request.jobId
    clip_id = request.clipId
    
    job = job_manager.load_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    try:
        # Find the clip in the job results
        clip_data = None
        if job.get("results"):
            for clip in job["results"]:
                if str(clip.get("id")) == clip_id:
                    clip_data = clip
                    break
        
        if not clip_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Clip {clip_id} not found in job {job_id}"
            )
        
        # Find the video file
        local_job_dir = Path(settings.LOCAL_OUTPUT_DIR) / job_id
        clips_dir = local_job_dir / "clips"
        original_clips_dir = local_job_dir / "original_clips"
        
        # Look for the clip file in both directories
        clip_file = None
        for clips_search_dir in [clips_dir, original_clips_dir]:
            if clips_search_dir.exists():
                for file in clips_search_dir.glob("*.mp4"):
                    if clip_id in file.stem or clip_data.get("title", "").replace(" ", "_") in file.stem:
                        clip_file = file
                        break
                if clip_file:
                    break
        
        if not clip_file or not clip_file.exists():
            # For demo purposes, generate mock captions optimized for word-by-word
            print(f"⚠️ Video file not found for clip {clip_id}, generating mock captions")
            mock_captions = [
                CaptionSegment(start=0.0, end=3.0, text="This will absolutely blow your mind!", confidence=0.95),
                CaptionSegment(start=3.0, end=6.5, text="You won't believe what happens next", confidence=0.92),
                CaptionSegment(start=6.5, end=10.0, text="This game changing technique just got revealed", confidence=0.88),
                CaptionSegment(start=10.0, end=13.5, text="Your life will never be the same again", confidence=0.91),
                CaptionSegment(start=13.5, end=16.0, text="Watch this incredible transformation", confidence=0.89)
            ]
            
            return GenerateCaptionsResponse(
                status="success",
                message="Mock captions generated successfully",
                captions=mock_captions,
                previewUrl=f"/clips/{job_id}/clips/{clip_file.name if clip_file else 'preview.mp4'}"
            )
        
        print(f"🎙️ Generating captions for {clip_file}")
        
        # Transcribe the video
        transcript_segments = transcribe_video(str(clip_file))
        
        # Convert to caption segments
        captions = [
            CaptionSegment(
                start=segment["start"],
                end=segment["end"],
                text=segment["text"],
                confidence=segment.get("confidence", 0.0)
            )
            for segment in transcript_segments
        ]
        
        print(f"✅ Generated {len(captions)} caption segments")
        
        return GenerateCaptionsResponse(
            status="success",
            message=f"Generated {len(captions)} caption segments",
            captions=captions,
            previewUrl=f"/clips/{job_id}/clips/{clip_file.name}"
        )
        
    except Exception as e:
        print(f"❌ Caption generation failed: {e}")
        # Return mock captions as fallback optimized for word-by-word
        mock_captions = [
            CaptionSegment(start=0.0, end=3.0, text="This will absolutely blow your mind!", confidence=0.95),
            CaptionSegment(start=3.0, end=6.5, text="You won't believe what happens next", confidence=0.92),
            CaptionSegment(start=6.5, end=10.0, text="This game changing technique just got revealed", confidence=0.88),
            CaptionSegment(start=10.0, end=13.5, text="Your life will never be the same again", confidence=0.91),
            CaptionSegment(start=13.5, end=16.0, text="Watch this incredible transformation", confidence=0.89)
        ]
        
        return GenerateCaptionsResponse(
            status="success",
            message="Mock captions generated (demo mode)",
            captions=mock_captions
        )


@app.post("/captions/apply", response_model=ApplyCaptionsResponse)
async def apply_captions(request: ApplyCaptionsRequest):
    """Apply captions to a video clip with YouTube Shorts styling"""
    
    if not CAPTION_PROCESSOR_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Caption processing is not available"
        )
    
    job_id = request.jobId
    clip_id = request.clipId
    
    job = job_manager.load_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    try:
        # Find the video file
        local_job_dir = Path(settings.LOCAL_OUTPUT_DIR) / job_id
        clips_dir = local_job_dir / "clips"
        original_clips_dir = local_job_dir / "original_clips"
        captioned_clips_dir = local_job_dir / "captioned"
        
        # Create captioned directory
        captioned_clips_dir.mkdir(exist_ok=True)
        
        # Look for the clip file
        input_file = None
        for clips_search_dir in [clips_dir, original_clips_dir]:
            if clips_search_dir.exists():
                for file in clips_search_dir.glob("*.mp4"):
                    if clip_id in file.stem:
                        input_file = file
                        break
                if input_file:
                    break
        
        if not input_file or not input_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video file for clip {clip_id} not found"
            )
        
        # Create output filename
        safe_clip_id = "".join(c for c in clip_id if c.isalnum() or c in ('-', '_'))
        output_filename = f"{safe_clip_id}_captioned.mp4"
        output_file = captioned_clips_dir / output_filename
        
        print(f"🎬 Applying captions to {input_file} -> {output_file}")
        
        # Convert Pydantic models to dictionaries for the video processor
        captions_dict = [caption.dict() for caption in request.captions]
        style_dict = request.style.dict()
        
        # Apply captions using the caption burner
        success = apply_captions_to_video(
            str(input_file),
            str(output_file),
            captions_dict,
            style_dict
        )
        
        if success and output_file.exists():
            # Generate URL for the captioned video
            output_url = f"/clips/{job_id}/captioned/{output_filename}"
            
            print(f"✅ Successfully applied captions to {output_filename}")
            
            return ApplyCaptionsResponse(
                status="success",
                message="Captions applied successfully",
                outputPath=str(output_file),
                previewUrl=output_url
            )
        else:
            raise Exception("Caption application failed")
            
    except Exception as e:
        print(f"❌ Caption application failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply captions: {str(e)}"
        )


@app.post("/finalize/{job_id}", response_model=FinalizeResponse)
async def finalize_clips(job_id: str, request: FinalizeRequest):
    """Re-process clips with edited timings to create final trimmed videos"""
    
    import shutil
    import subprocess
    
    job = job_manager.load_job(job_id)
    
    if not job:
        print(f"❌ Finalize: Job {job_id} not found in storage or memory")
        print(f"📊 Available jobs: {list(job_manager.jobs.keys())}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    if job["status"] != "complete":
        print(f"❌ Finalize: Job {job_id} status is {job['status']}, expected 'complete'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job must be completed before finalizing. Current status: {job['status']}"
        )
    
    try:
        edited_clips = request.edited_clips
        print(f"🎬 Starting finalization for job {job_id} with {len(edited_clips)} clips")
        
        local_job_dir = Path(settings.LOCAL_OUTPUT_DIR) / job_id
        clips_dir = local_job_dir / "clips"  # This is where the original clips are stored
        original_clips_dir = local_job_dir / "original_clips" 
        finalized_clips_dir = local_job_dir / "finalized_clips"
        
        # Verify job output directory exists
        if not local_job_dir.exists():
            raise Exception(f"Job output directory not found: {local_job_dir}")
        
        # Verify clips directory exists (where original clips are stored)
        if not clips_dir.exists():
            raise Exception(f"Clips directory not found: {clips_dir}")
        
        # Create directories
        finalized_clips_dir.mkdir(exist_ok=True)
        
        # Create original_clips directory but DON'T move files yet
        original_clips_dir.mkdir(exist_ok=True)
        
        # Only move files if original_clips is empty AND we're actually finalizing
        moved_files = 0
        if not any(original_clips_dir.glob("*.mp4")) and clips_dir.exists():
            # Copy (don't move) existing clip files from clips/ to original_clips/ to preserve access
            for file in clips_dir.glob("*.mp4"):
                shutil.copy2(str(file), str(original_clips_dir / file.name))
                moved_files += 1
            print(f"📁 Copied {moved_files} original clips to original_clips/ directory (preserving clips/ access)")
        else:
            print(f"📁 Original clips already in original_clips/ directory")
        
        finalized_results = []
        
        for i, edited_clip in enumerate(edited_clips):
            try:
                print(f"🔄 Processing clip {i+1}/{len(edited_clips)}: {edited_clip.title}")
                
                # First, check if there's a captioned version of this clip
                captioned_clips_dir = local_job_dir / "captioned"
                captioned_file = None
                if captioned_clips_dir.exists():
                    for file in captioned_clips_dir.glob("*.mp4"):
                        if edited_clip.id in file.stem:
                            captioned_file = file
                            print(f"🎬 Found captioned version: {captioned_file.name}")
                            break
                
                # Find the original clip file (fallback if no captioned version)
                original_file = None
                # First try original_clips directory
                for file in original_clips_dir.glob("*.mp4"):
                    if edited_clip.id in file.stem or edited_clip.title.replace(" ", "_") in file.stem:
                        original_file = file
                        break
                
                # If not found in original_clips, try clips directory
                if not original_file and clips_dir.exists():
                    for file in clips_dir.glob("*.mp4"):
                        if edited_clip.id in file.stem or edited_clip.title.replace(" ", "_") in file.stem:
                            original_file = file
                            break
                
                # Use captioned version if available, otherwise use original
                source_file = captioned_file if captioned_file else original_file
                
                if not source_file:
                    print(f"⚠️ Warning: Could not find source file for clip {edited_clip.id}")
                    print(f"📁 Available original files: {[f.name for f in original_clips_dir.glob('*.mp4')]}")
                    print(f"📁 Available clips files: {[f.name for f in clips_dir.glob('*.mp4')] if clips_dir.exists() else 'None'}")
                    print(f"📁 Available captioned files: {[f.name for f in captioned_clips_dir.glob('*.mp4')] if captioned_clips_dir.exists() else 'None'}")
                    continue
                
                print(f"📂 Using source file: {source_file.name} ({'captioned' if captioned_file else 'original'})")
                
                # Create finalized filename
                safe_title = "".join(c for c in edited_clip.title if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_title = safe_title.replace(' ', '_')
                finalized_filename = f"{safe_title}_final.mp4"
                finalized_path = finalized_clips_dir / finalized_filename
                
                # If using captioned version, we may not need to trim (it might already be trimmed)
                if captioned_file:
                    # For captioned files, just copy or do minimal processing
                    print(f"🎬 Using captioned version: {captioned_file.name}")
                    
                    # Check if we still need to trim the captioned file
                    clip_original_start = edited_clip.start_time
                    relative_start = max(0, edited_clip.editedStart - clip_original_start)
                    relative_end = edited_clip.editedEnd - clip_original_start
                    clip_duration = edited_clip.end_time - edited_clip.start_time
                    relative_end = min(relative_end, clip_duration)
                    
                    start_time = relative_start
                    end_time = relative_end
                    duration = end_time - start_time
                    
                    # If the times haven't changed much, just copy the captioned file
                    if abs(relative_start) < 0.5 and abs(relative_end - clip_duration) < 0.5:
                        print(f"📋 Copying captioned file directly (no additional trimming needed)")
                        shutil.copy2(str(captioned_file), str(finalized_path))
                        duration = clip_duration
                    else:
                        print(f"✂️ Trimming captioned file: {start_time:.1f}s to {end_time:.1f}s (duration: {duration:.1f}s)")
                else:
                    # Convert absolute timestamps to relative timestamps within the clip
                    # Each clip was extracted from a specific segment of the original video
                    clip_original_start = edited_clip.start_time  # Where this clip starts in the original video
                    
                    # Calculate relative timestamps within the clip (0-based)
                    relative_start = max(0, edited_clip.editedStart - clip_original_start)
                    relative_end = edited_clip.editedEnd - clip_original_start
                    
                    # Ensure we don't exceed the clip boundaries
                    clip_duration = edited_clip.end_time - edited_clip.start_time
                    relative_end = min(relative_end, clip_duration)
                    
                    start_time = relative_start
                    end_time = relative_end
                    duration = end_time - start_time
                    
                    print(f"✂️ Trimming {source_file.name}: {start_time:.1f}s to {end_time:.1f}s (duration: {duration:.1f}s)")
                    print(f"📊 Original clip range: {clip_original_start:.1f}s-{edited_clip.end_time:.1f}s, edited range: {edited_clip.editedStart:.1f}s-{edited_clip.editedEnd:.1f}s")
                
                # Validate duration
                if duration <= 0:
                    print(f"⚠️ Invalid duration {duration:.1f}s for clip {edited_clip.title} - skipping")
                    continue
                
                # Use FFmpeg to trim the video (only if we haven't already copied)
                
                # Skip FFmpeg processing if we already copied the captioned file
                if not (captioned_file and abs(relative_start) < 0.5 and abs(relative_end - clip_duration) < 0.5):
                    ffmpeg_cmd = [
                        'ffmpeg', '-y',  # -y to overwrite output files
                        '-i', str(source_file),
                        '-ss', str(start_time),  # Start time within the clip
                        '-t', str(duration),     # Duration to extract
                        '-c', 'copy',            # Copy without re-encoding for speed
                        str(finalized_path)
                    ]
                    
                    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        print(f"⚠️ FFmpeg copy failed, trying with re-encoding: {result.stderr}")
                        # Try with re-encoding if copy fails
                        ffmpeg_cmd = [
                            'ffmpeg', '-y',
                            '-i', str(source_file),
                            '-ss', str(start_time),
                            '-t', str(duration),
                            '-c:v', 'libx264', '-c:a', 'aac',
                            str(finalized_path)
                        ]
                        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                    
                    # Check if processing succeeded
                    if result.returncode != 0 or not finalized_path.exists():
                        print(f"❌ FFmpeg processing failed for {edited_clip.title}")
                        continue
                
                if finalized_path.exists():
                    # Add to finalized results
                    relative_path = f"/clips/{job_id}/finalized_clips/{finalized_filename}"
                    
                    finalized_results.append({
                        "id": edited_clip.id,
                        "title": edited_clip.title,
                        "path": relative_path,
                        "url_path": relative_path,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration": format_duration(duration),
                        "startTime": f"{int(start_time//60):02d}:{int(start_time%60):02d}",
                        "endTime": f"{int(end_time//60):02d}:{int(end_time%60):02d}",
                        "text": edited_clip.text,
                        "caption": edited_clip.caption,
                        "hashtags": edited_clip.hashtags,
                        "original_file": f"/clips/{job_id}/original_clips/{original_file.name}" if original_file else None,
                        "captioned_source": f"/clips/{job_id}/captioned/{captioned_file.name}" if captioned_file else None
                    })
                    
                    source_type = "captioned" if captioned_file else "original"
                    print(f"✅ Successfully created finalized clip: {finalized_filename} (from {source_type} source)")
                else:
                    print(f"❌ Failed to create finalized clip for {edited_clip.title}")
                    if 'result' in locals():
                        print(f"FFmpeg stderr: {result.stderr}")
                    
            except Exception as e:
                print(f"❌ Error processing clip {edited_clip.id}: {e}")
                continue
        
        # Update job with finalized results
        job["finalized_results"] = finalized_results
        job["finalized_at"] = str(Path().cwd())  # timestamp placeholder
        job_manager.save_job(job_id, job)
        
        print(f"🎉 Finalization completed: {len(finalized_results)}/{len(edited_clips)} clips processed successfully")
        
        return {
            "status": "success",
            "message": f"Successfully finalized {len(finalized_results)} clips",
            "finalized_clips": finalized_results,
            "organization": {
                "original_clips": f"/clips/{job_id}/original_clips/",
                "finalized_clips": f"/clips/{job_id}/finalized_clips/"
            }
        }
        
    except Exception as e:
        print(f"❌ Finalization error for job {job_id}: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to finalize clips: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 