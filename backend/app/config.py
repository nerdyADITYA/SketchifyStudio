from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Sketchify Studio API"
    app_env: str = "development"
    frontend_origin: str = "http://localhost:5173"

    max_upload_size_mb: int = 10
    min_image_width: int = 32
    min_image_height: int = 32
    max_image_width: int = 8000
    max_image_height: int = 8000
    max_image_pixels: int = 25_000_000

    min_output_width: int = 16
    min_output_height: int = 16
    max_output_width: int = 8000
    max_output_height: int = 8000
    max_output_pixels: int = 25_000_000

    max_concurrent_jobs: int = 2
    processing_timeout_seconds: int = 90

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.frontend_origin.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
