from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import os
import subprocess
import tempfile
import uuid
import requests
from pathlib import Path

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
    transition_type: str = "fade"
    user_id: str
    text_position: str
    hook_text: str
    selected_avatar: int

class StitchResponse(BaseModel):
    """Response model for video stitching"""
    status: str
    output_url: str

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
    Endpoint to stitch multiple videos together with text overlay
    """
    try:
        # Validate input
        if not request.video_urls:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No videos provided for stitching"
            )
        
        # Create temp directory for processing
        temp_dir = tempfile.mkdtemp()
        output_filename = f"{uuid.uuid4()}.mp4"
        output_path = os.path.join(temp_dir, output_filename)
        
        # 1. Download the video
        input_video_path = os.path.join(temp_dir, "input.mp4")
        
        # If the video URL is a local path (starts with /), use the local file
        # Otherwise, download from URL
        video_url = request.video_urls[0]
        if video_url.startswith('/'):
            # For local development, prepend with your public directory path
            # Adjust this path to match your project structure
            base_path = os.path.join(os.getcwd(), "../one-stop-marketing/public")
            input_video_path = os.path.join(base_path, video_url.lstrip('/'))
        else:
            # Download from remote URL
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(input_video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        # 2. Prepare text overlay based on position
        # Create a temporary text file for the overlay
        text_file = os.path.join(temp_dir, "text.txt")
        with open(text_file, 'w') as f:
            f.write(request.hook_text)
        
        # Determine text position parameters
        if request.text_position == "top":
            y_position = "h*0.1"  # 10% from the top
        elif request.text_position == "middle":
            y_position = "h*0.5"  # Center
        else:  # bottom
            y_position = "h*0.9"  # 10% from the bottom
        
        # 3. Use FFmpeg to add text overlay
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', input_video_path,
            '-vf', f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=24:fontcolor=white:x=(w-text_w)/2:y={y_position}:text='{request.hook_text}':box=1:boxcolor=black@0.5:boxborderw=5",
            '-c:a', 'copy',
            '-y',  # Overwrite output file if it exists
            output_path
        ]
        
        # Execute FFmpeg command
        process = subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        if process.returncode != 0:
            print(f"FFmpeg error: {process.stderr.decode()}")
            raise Exception("Failed to process video with FFmpeg")
        
        # 4. For this example, we'll just return the path to the processed file
        # In a real application, you would upload this to cloud storage
        
        # Create a directory for output videos if it doesn't exist
        output_dir = os.path.join(os.getcwd(), "public", "output_videos")
        os.makedirs(output_dir, exist_ok=True)
        
        # Copy the output file to the public directory
        final_output_path = os.path.join(output_dir, output_filename)
        with open(output_path, 'rb') as src, open(final_output_path, 'wb') as dst:
            dst.write(src.read())
        
        # Return the URL to the processed video
        return {
            "status": "success",
            "output_url": f"/output_videos/{output_filename}"
        }

    except Exception as e:
        print(f"Error processing video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stitch videos: {str(e)}"
        )
    finally:
        # Clean up temporary files
        if 'temp_dir' in locals():
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
