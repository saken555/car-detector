from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    
    APP_TITLE: str = "car detect"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    
    VIDEO_SOURCE: str = "sample.mp4"  # Путь к локальному видеофайлу 
    FRAME_SKIP: int = 5               # Обрабатывать только каждый N-й кадр (если 1 - обрабатывать каждый)
    MIN_CONF: float = 0.5             # Минимальная степень уверенности (0.0 - 1.0)
    YOLO_MODEL_PATH: str = "yolov8n.pt"
    TARGET_CLASSES: List[int] = [2]   # Классы COCO: 2 = car

    BASE_DIR: Path = Path(__file__).resolve().parent
    DETECTIONS_DIR: Path = BASE_DIR / "media" / "detections"

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

settings.DETECTIONS_DIR.mkdir(parents=True, exist_ok=True)
