import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Configuration Validation
    print("-" * 39)
    print("LLM Configuration\n")
    
    # In the current architecture, Gemini is the hardcoded active provider in services
    active_provider = "Gemini"
    chat_model = settings.GEMINI_MODEL
    embedding_model = settings.GEMINI_EMBEDDING_MODEL
    env_name = "Development" if settings.DEBUG else "Production"
    
    print(f"Provider:\n{active_provider}\n")
    print(f"Chat Model:\n{chat_model}\n")
    print(f"Embedding Model:\n{embedding_model}\n")
    print(f"Environment:\n{env_name}\n")
    
    if not settings.GEMINI_API_KEY:
        print("API Key:\nMissing\n")
        print("Provider Validation:\nFailed\n")
        print("-" * 39)
        raise RuntimeError("Invalid Gemini configuration. Missing GEMINI_API_KEY. Application startup aborted.")
    
    print("API Key:\nLoaded\n")
    
    if not chat_model or not chat_model.strip():
        print("Provider Validation:\nFailed\n")
        print("-" * 39)
        raise RuntimeError("Invalid Gemini configuration. Configured chat model is empty. Application startup aborted.")
        
    if not embedding_model or not embedding_model.strip():
        print("Provider Validation:\nFailed\n")
        print("-" * 39)
        raise RuntimeError("Invalid Gemini configuration. Configured embedding model is empty. Application startup aborted.")

    import os
    if os.getenv("ENABLE_PROVIDER_VALIDATION", "false").lower() == "true":
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            # Lightweight verification
            list(client.models.list())
        except Exception as e:
            print("Provider Validation:\nFailed\n")
            print("-" * 39)
            raise RuntimeError(f"Configured model is unavailable or API key is invalid: {e}. Application startup aborted.")

    print("Provider Validation:\nPassed\n")
    print("-" * 39)
    
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)


if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }