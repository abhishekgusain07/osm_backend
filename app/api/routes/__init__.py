from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.info import router as info_router

# Main router that combines all API endpoints
router = APIRouter()

# Include all route modules here
router.include_router(health_router, tags=["health"])
router.include_router(info_router, tags=["info"])
