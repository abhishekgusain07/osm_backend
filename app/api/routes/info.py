from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import os

router = APIRouter()

class InfoResponse(BaseModel):
    """Health check response model"""
    status: str
    version: str
    info: str

class StitchRequest(BaseModel):
    """Request model for video stitching"""
    video_urls: List[str]
    output_name: str
    transition_type: str = "fade"  # default transition
    user_id: str

class StitchResponse(BaseModel):
    """Response model for video stitching"""
    status: str
    output_url: str
    duration: float

@router.get("/info", response_model=InfoResponse, status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Info check endpoint to tell what this API is about
    """
    return {
        "status": "operational",
        "version": "0.1.0",
        "info": "stich the ugc video together",
    }

@router.post("/stitch", response_model=StitchResponse, status_code=status.HTTP_200_OK)
async def stitch_videos(request: StitchRequest) -> Dict[str, Any]:
    """
    Endpoint to stitch multiple videos together
    
    Args:
        request: StitchRequest containing video URLs and parameters
        
    Returns:
        Dict containing status and output video URL
        
    Raises:
        HTTPException: If videos can't be processed or stitching fails
    """
    try:
        # Validate input videos
        if not request.video_urls:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No videos provided for stitching"
            )
            
        if len(request.video_urls) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 videos are required for stitching"
            )

        # TODO: Implement video stitching logic here
        # 1. Download videos from URLs
        # 2. Process videos (apply transitions, etc.)
        # 3. Stitch videos together
        # 4. Upload result to storage
        # 5. Return output URL

        # Placeholder response
        return {
            "status": "success",
            "output_url": f"https://storage.example.com/stitched/{request.output_name}.mp4",
            "duration": 120.5  # Duration in seconds
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stitch videos: {str(e)}"
        )
