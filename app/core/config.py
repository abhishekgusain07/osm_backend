# app/core/config.py
from typing import List
from pydantic import BaseSettings, AnyHttpUrl
import json

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    API_PREFIX: str = "/api"
    PROJECT_NAME: str = "FastAPI Backend Service"
    
    # CORS settings (in production, set specific origins)
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Environment settings
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name == "ALLOWED_ORIGINS":
                try:
                    return json.loads(raw_val)  # Try to parse as JSON first
                except json.JSONDecodeError:
                    return [origin.strip() for origin in raw_val.split(",")]  # Fall back to comma-separated list
            return cls.json_loads(raw_val)  # Default behavior for other fields

# Singleton instance
settings = Settings()