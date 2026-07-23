from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "JyotishAI API"
    APP_VERSION: str = "1.0.0"
    
    # Server Settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost"]

    # Database Settings
    DATABASE_URL: str

    # JWT Settings
    # Removed default value to force environment variable requirement
    SECRET_KEY: str 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # LLM API Keys
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-flash-latest"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"
    GEMINI_TIMEOUT: int = 30
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    ASTROLOGY_API_KEY: Optional[str] = None

    # Local LLM Configuration
    LOCAL_LLM_URL: Optional[str] = "http://localhost:11434"
    LOCAL_LLM_TIMEOUT: int = 60

    # ChromaDB Configuration
    CHROMA_PERSIST_DIR: str = "chroma_db"
    CHROMA_HOST: Optional[str] = None
    CHROMA_PORT: Optional[int] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
