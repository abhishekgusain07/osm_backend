from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    version: str
    service: str

@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint to verify API is operational.
    Returns basic service info and status.
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "FastAPI Backend Service",
    }
