"""Configuración del Sistema Biométrico
Todas las variables se pueden sobreescribir con un archivo .env
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ========================================
    # BASE DE DATOS
    # ========================================
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "biometric_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DATABASE_URL: str = ""

    @property
    def db_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # ========================================
    # RECONOCIMIENTO FACIAL (InsightFace)
    # ========================================
    SIMILARITY_THRESHOLD: float = 0.45
    MIN_FACE_QUALITY: float = 40.0

    # ========================================
    # UBICACIÓN GPS
    # ========================================
    MAX_DISTANCE_METERS: int = 200

    # ========================================
    # SEGURIDAD / JWT
    # ========================================
    SECRET_KEY: str = "cambiar-en-produccion-con-variable-de-entorno"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480  # 8 horas

    # ========================================
    # CORS
    # ========================================
    CORS_ORIGINS: str = "*"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
