from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_TITLE: str = "Car Detection Service"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # ML & CV Parameters
    VIDEO_SOURCE: str = "sample.mp4"
    FRAME_SKIP: int = 5 # каждый 5-ый кадр
    MIN_CONF: float = 0.5 # порог уверенности модели
    MAX_SAVED_FRAMES: int = 10 # макс. сколко изображений сохранять  
    YOLO_MODEL_PATH: str = "yolov8n.pt"
    TARGET_CLASSES: List[int] = [2]  # COCO Class 2 = это авто

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent
    DETECTIONS_DIR: Path = BASE_DIR / "media" / "detections"

    # Infrastructure
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "video_db"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
