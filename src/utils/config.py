from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables or .env file.
    """
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    google_maps_api_key: str = ""

    sms_provider: str = "console"
    sms_api_key: str = ""
    sms_sender_id: str = "SIHAGR"
    sms_endpoint: str = ""
    sms_dry_run: bool = True
    open_meteo_base_url: str = "https://api.open-meteo.com/v1"
    imd_api_key: str = ""
    
    database_url: str = "sqlite:///./data/weather.db"
    
    default_lat: float = 23.275
    default_lon: float = 77.335
    default_region: str = "Phanda, Bhopal"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache()
def get_settings() -> Settings:
    """
    Return application settings using a singleton pattern.
    """
    return Settings()
