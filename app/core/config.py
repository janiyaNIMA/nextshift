from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "NextShift"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/nextshift?charset=utf8mb4"

    JWT_SECRET_KEY: str = "insecure-development-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    FIRST_ADMIN_NAME: str = "System Administrator"
    FIRST_ADMIN_EMAIL: str = "admin@nextshift.local"
    FIRST_ADMIN_PASSWORD: str = "AdminSecurePassword123!"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
