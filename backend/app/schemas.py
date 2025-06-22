from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Any, Literal


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


class EditedClip(BaseModel):
    """Model for edited clip data sent to finalize endpoint"""
    id: str
    title: str
    editedStart: float
    editedEnd: float
    originalStart: float
    originalEnd: float
    path: str
    start_time: float
    end_time: float
    text: Optional[str] = ""
    caption: Optional[str] = ""
    hashtags: Optional[List[str]] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "clip_1",
                "title": "Opening Hook",
                "editedStart": 10.5,
                "editedEnd": 25.3,
                "originalStart": 15.0,
                "originalEnd": 35.0,
                "path": "/clips/job_123/clips/clip_1.mp4",
                "start_time": 15.0,
                "end_time": 35.0,
                "text": "Welcome to today's video!",
                "caption": "This will blow your mind! 🤯",
                "hashtags": ["viral", "mindblown"]
            }
        }


class FinalizeRequest(BaseModel):
    """Request model for finalizing edited clips"""
    edited_clips: List[EditedClip]
    
    class Config:
        json_schema_extra = {
            "example": {
                "edited_clips": [
                    {
                        "id": "clip_1",
                        "title": "Opening Hook",
                        "editedStart": 10.5,
                        "editedEnd": 25.3,
                        "originalStart": 15.0,
                        "originalEnd": 35.0,
                        "path": "/clips/job_123/clips/clip_1.mp4",
                        "start_time": 15.0,
                        "end_time": 35.0,
                        "text": "Welcome to today's video!",
                        "caption": "This will blow your mind! 🤯",
                        "hashtags": ["viral", "mindblown"]
                    }
                ]
            }
        }


class FinalizedClip(BaseModel):
    """Model for finalized clip response"""
    id: str
    title: str
    path: str
    url_path: str
    start_time: float
    end_time: float
    duration: str  # Changed to string for formatted duration (e.g., "14.6s" or "1:23")
    startTime: str
    endTime: str
    text: str
    caption: str
    hashtags: List[str]
    original_file: str


class FinalizeResponse(BaseModel):
    """Response model for finalize operation"""
    status: str
    message: str
    finalized_clips: List[FinalizedClip]
    organization: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Successfully finalized 3 clips",
                "finalized_clips": [],
                "organization": {
                    "original_clips": "/clips/job_123/original_clips/",
                    "finalized_clips": "/clips/job_123/finalized_clips/"
                }
            }
        }


class ClipMetadata(BaseModel):
    """Model for clip metadata"""
    id: int
    filename: str
    title: str
    start_time: float
    end_time: float
    duration: float
    text: str
    caption: str
    hashtags: List[str]
    url_path: str
    is_demo: Optional[bool] = False


class CaptionSegment(BaseModel):
    """Model for a single caption segment"""
    start: float
    end: float
    text: str
    confidence: Optional[float] = None


class CaptionStyle(BaseModel):
    """Model for caption styling options"""
    fontSize: int = 48
    fontColor: str = "#FFFFFF"
    backgroundColor: str = "#000000"
    backgroundOpacity: float = 0.7
    outlineColor: str = "#000000"
    outlineWidth: int = 3
    position: Literal["top", "center", "bottom"] = "center"
    animation: Literal["none", "pop", "slide", "typewriter"] = "pop"


class GenerateCaptionsRequest(BaseModel):
    """Request model for generating captions"""
    jobId: str
    clipId: str
    style: Optional[CaptionStyle] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "jobId": "123e4567-e89b-12d3-a456-426614174000",
                "clipId": "clip_1",
                "style": {
                    "fontSize": 48,
                    "fontColor": "#FFFFFF",
                    "backgroundColor": "#000000",
                    "backgroundOpacity": 0.7,
                    "outlineColor": "#000000",
                    "outlineWidth": 3,
                    "position": "center",
                    "animation": "pop"
                }
            }
        }


class GenerateCaptionsResponse(BaseModel):
    """Response model for caption generation"""
    status: str
    message: str
    captions: List[CaptionSegment]
    previewUrl: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Captions generated successfully",
                "captions": [
                    {
                        "start": 0.0,
                        "end": 2.5,
                        "text": "This will blow your mind!",
                        "confidence": 0.95
                    }
                ],
                "previewUrl": "/clips/job_123/previews/clip_1_preview.mp4"
            }
        }


class ApplyCaptionsRequest(BaseModel):
    """Request model for applying captions to video"""
    jobId: str
    clipId: str
    captions: List[CaptionSegment]
    style: CaptionStyle
    
    class Config:
        json_schema_extra = {
            "example": {
                "jobId": "123e4567-e89b-12d3-a456-426614174000",
                "clipId": "clip_1",
                "captions": [
                    {
                        "start": 0.0,
                        "end": 2.5,
                        "text": "This will blow your mind!",
                        "confidence": 0.95
                    }
                ],
                "style": {
                    "fontSize": 48,
                    "fontColor": "#FFFFFF",
                    "backgroundColor": "#000000",
                    "backgroundOpacity": 0.7,
                    "outlineColor": "#000000",
                    "outlineWidth": 3,
                    "position": "center",
                    "animation": "pop"
                }
            }
        }


class ApplyCaptionsResponse(BaseModel):
    """Response model for applying captions"""
    status: str
    message: str
    outputPath: str
    previewUrl: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Captions applied successfully",
                "outputPath": "/clips/job_123/captioned/clip_1_captioned.mp4",
                "previewUrl": "/clips/job_123/captioned/clip_1_captioned.mp4"
            }
        }


class JobStatusResponse(BaseModel):
    """Response model for job status queries"""
    status: str
    message: str
    results: Optional[List[Any]] = None  # Can be List[str] or List[ClipMetadata]
    is_demo: Optional[bool] = False
    metadata: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "complete",
                "message": "Processing completed successfully",
                "results": [
                    {
                        "id": 1,
                        "filename": "clip_1.mp4",
                        "title": "Opening Hook",
                        "start_time": 15.0,
                        "end_time": 35.0,
                        "duration": 20.0,
                        "text": "Welcome to today's video!",
                        "caption": "This will blow your mind! 🤯",
                        "hashtags": ["#viral", "#mindblown"],
                        "url_path": "/clips/job_123/clips/clip_1.mp4",
                        "is_demo": False
                    }
                ],
                "is_demo": False
            }
        } 