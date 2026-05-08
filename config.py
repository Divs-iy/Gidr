import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # This will look for a .env file or environment variable
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "your_fallback_key_here")
    PROJECT_NAME: str = "Gidr AI Invoice Parser"
    DEBUG: bool = True

    class Config:
        env_file = ".env"

settings = Settings()