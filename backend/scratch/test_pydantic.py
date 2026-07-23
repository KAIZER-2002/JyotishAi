from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
class S(BaseSettings):
    GEMINI_API_KEY: Optional[str] = None
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
print(repr(S().GEMINI_API_KEY))
