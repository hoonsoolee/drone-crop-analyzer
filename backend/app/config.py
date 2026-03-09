from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "Drone Crop Analyzer"
    VERSION: str = "0.1.0"
    DEBUG: bool = True

    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"

    MAX_UPLOAD_SIZE_MB: int = 500
    ALLOWED_EXTENSIONS: list[str] = [".jpg", ".jpeg", ".png", ".tif", ".tiff"]

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
