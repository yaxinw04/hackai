from pydantic import BaseModel, HttpUrl
from typing import List, Optional


class ProcessRequest(BaseModel):
    """Request model for processing a YouTube video into shorts"""
    url: str
    prompt: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "prompt": "Create engaging short clips about the main topics"
            }
        }


class ProcessResponse(BaseModel):
    """Response model for starting a processing job"""
    job_id: str
    status: str
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "pending",
                "message": "Job started successfully"
            }
        }


class JobStatusResponse(BaseModel):
    """Response model for job status queries"""
    status: str
    message: str
    results: Optional[List[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "complete",
                "message": "Processing completed successfully",
                "results": [
                    "/clips/job_123_clip_1.mp4",
                    "/clips/job_123_clip_2.mp4"
                ]
            }
        } 