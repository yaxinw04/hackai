import os
import uuid
import traceback
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .schemas import ProcessRequest, ProcessResponse, JobStatusResponse

# Import the video processing pipeline
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from ml_stuff.pipeline import run_processing_pipeline
    VIDEO_PROCESSOR_AVAILABLE = True
except ImportError as e:
    VIDEO_PROCESSOR_AVAILABLE = False
    print(f"Warning: video processing pipeline not found: {e}")
    print("Make sure ml_stuff/pipeline.py exists and dependencies are installed")

app = FastAPI(
    title="YouTube to Shorts API",
    description="API for converting YouTube videos to short clips",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage (in production, use a proper database)
jobs: Dict[str, Dict[str, Any]] = {}

# Setup static file serving for clips
output_dir = Path(__file__).parent / "output_clips"
output_dir.mkdir(exist_ok=True)

app.mount("/clips", StaticFiles(directory=str(output_dir)), name="clips")


async def process_video_background(job_id: str, url: str, prompt: str):
    """Background task to process video using the ml_stuff pipeline"""
    try:
        # Update job status to processing
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["message"] = "Processing video..."
        
        if not VIDEO_PROCESSOR_AVAILABLE:
            raise Exception("Video processing pipeline is not available")
        
        # Call the ml_stuff processing pipeline
        output_paths = run_processing_pipeline(
            job_id=job_id,
            url=url,
            prompt=prompt,
            output_dir=str(output_dir)
        )
        
        # Convert absolute paths to relative URLs for the frontend
        relative_paths = []
        for path in output_paths:
            if os.path.exists(path):
                filename = os.path.basename(path)
                relative_paths.append(f"/clips/{filename}")
        
        # Update job status to complete
        jobs[job_id]["status"] = "complete"
        jobs[job_id]["message"] = "Processing completed successfully"
        jobs[job_id]["results"] = relative_paths
        
    except Exception as e:
        # Update job status to failed
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Processing failed: {str(e)}"
        jobs[job_id]["error"] = traceback.format_exc()
        print(f"Job {job_id} failed: {e}")
        print(traceback.format_exc())


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "YouTube to Shorts API",
        "version": "1.0.0",
        "endpoints": {
            "process": "POST /process",
            "status": "GET /status/{job_id}",
            "clips": "GET /clips/{filename}"
        }
    }


@app.post("/process", response_model=ProcessResponse)
async def process_video(request: ProcessRequest, background_tasks: BackgroundTasks):
    """Start processing a YouTube video into shorts"""
    
    if not VIDEO_PROCESSOR_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Video processing pipeline is not available. Check that ml_stuff/pipeline.py exists and dependencies are installed."
        )
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    jobs[job_id] = {
        "status": "pending",
        "message": "Job queued for processing",
        "url": request.url,
        "prompt": request.prompt,
        "results": None
    }
    
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
    
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job = jobs[job_id]
    
    return JobStatusResponse(
        status=job["status"],
        message=job["message"],
        results=job.get("results")
    )


@app.get("/jobs")
async def list_jobs():
    """List all jobs (for debugging)"""
    return {"jobs": jobs}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 