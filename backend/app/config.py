import os
from pathlib import Path
from typing import Optional

class Settings:
    """Production-ready configuration settings"""
    
    # Environment
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS settings
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # Storage settings
    USE_S3: bool = os.getenv("USE_S3", "false").lower() == "true"
    
    # S3 Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET: Optional[str] = os.getenv("S3_BUCKET")
    S3_BUCKET_URL: Optional[str] = os.getenv("S3_BUCKET_URL")  # CloudFront URL if using CDN
    
    # Local storage (fallback)
    LOCAL_OUTPUT_DIR: str = os.getenv("LOCAL_OUTPUT_DIR", str(Path(__file__).parent / "output_clips"))
    
    # Database (optional for advanced deployments)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # FFmpeg configuration
    FFMPEG_PATH: Optional[str] = os.getenv("FFMPEG_PATH")
    USE_SYSTEM_FFMPEG: bool = os.getenv("USE_SYSTEM_FFMPEG", "true").lower() == "true"
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
    MAX_JOBS_PER_USER: int = int(os.getenv("MAX_JOBS_PER_USER", "5"))
    
    # Video processing limits
    MAX_VIDEO_DURATION: int = int(os.getenv("MAX_VIDEO_DURATION", "3600"))  # 1 hour
    MAX_CLIP_COUNT: int = int(os.getenv("MAX_CLIP_COUNT", "10"))
    
    @property
    def base_url(self) -> str:
        """Get the base URL for video serving"""
        if self.USE_S3 and self.S3_BUCKET_URL:
            return self.S3_BUCKET_URL
        elif self.USE_S3 and self.S3_BUCKET:
            return f"https://{self.S3_BUCKET}.s3.{self.AWS_REGION}.amazonaws.com"
        else:
            return f"http://{self.HOST}:{self.PORT}/clips"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENV.lower() == "production"

# Global settings instance
settings = Settings() 