"""
Configuration Management using Pydantic Settings
Loads environment variables and provides type-safe config access
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    Application Settings - loads from .env file
    All values are type-validated by Pydantic
    """
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = True
    API_RELOAD: bool = True
    
    # Security
    SECRET_KEY: str
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    # Gemini AI (will be used in CHUNK 2.1)
    GEMINI_API_KEY: str = ""
    
    # File Upload Limits (will be used in CHUNK 1.2)
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = "pdf,docx"
    
    # Application Metadata
    APP_NAME: str = "Skill Assessment System"
    APP_VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Convert comma-separated extensions to list"""
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes"""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


# Global settings instance
settings = Settings()
