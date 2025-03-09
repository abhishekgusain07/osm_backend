from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import os
import subprocess
import tempfile
import uuid
import requests
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

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
    Endpoint to stitch multiple videos together with text overlay and upload to Cloudflare R2
    """
    try:
        # Debug: Print environment variables
        print(f"R2_ENDPOINT_URL: {os.getenv('R2_ENDPOINT_URL')}")
        print(f"R2_ACCESS_KEY_ID: {os.getenv('R2_ACCESS_KEY_ID')}")
        print(f"R2_SECRET_ACCESS_KEY: {os.getenv('R2_SECRET_ACCESS_KEY', 'REDACTED')[:3]}...")
        print(f"R2_BUCKET_NAME: {os.getenv('R2_BUCKET_NAME')}")
        
        # Debug: Print request data
        print(f"video_urls: {request.video_urls}")
        print(f"text_position: {request.text_position}")
        print(f"hook_text: {request.hook_text}")
        
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

        # Upload to Cloudflare R2
        try:
            # Debug: Before R2 client initialization
            print("About to initialize R2 client")
            
            # Initialize R2 client using boto3 (S3-compatible API)
            r2_client = boto3.client(
                's3',
                endpoint_url=os.getenv('R2_ENDPOINT_URL'),
                aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
                region_name='auto'
            )
            
            # Debug: After R2 client initialization
            print("R2 client initialized successfully")
            
            # R2 bucket name and object key (path)
            bucket_name = os.getenv('R2_BUCKET_NAME')
            object_key = f"videos/{request.user_id}/{output_filename}"
            
            # Upload file to R2
            r2_client.upload_file(
                Filename=final_output_path,
                Bucket=bucket_name,
                Key=object_key,
                ExtraArgs={
                    'ContentType': 'video/mp4',
                }
            )
            
            # Generate the URL for the uploaded file
            # For R2, we need to use the public URL format or a custom domain if configured
            if os.getenv('R2_PUBLIC_URL'):
                # If you have a custom domain or public bucket URL
                r2_url = f"{os.getenv('R2_PUBLIC_URL').rstrip('/')}/{object_key}"
            else:
                # Default R2 public URL format (if public access is enabled)
                r2_url = f"https://{bucket_name}.r2.dev/{object_key}"
            
            # Store video metadata in database
            # TODO: Implement database storage for video metadata
            
            return {
                "status": "success",
                "output_url": r2_url
            }
            
        except ClientError as e:
            print(f"R2 upload error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload video to Cloudflare R2: {str(e)}"
            )

    except Exception as e:
        print(f"Error processing video: {str(e)}")
        # Print the full traceback for better debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stitch videos: {str(e)}"
        )
    finally:
        # Clean up temporary files
        if 'temp_dir' in locals():
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        # Also remove the local output file after successful upload
        if 'final_output_path' in locals() and os.path.exists(final_output_path):
            os.remove(final_output_path)
