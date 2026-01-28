from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://sponge:sponge@localhost:5432/sponge"
    database_url_sync: str = "postgresql://sponge:sponge@localhost:5432/sponge"
    upload_dir: str = "./uploads"
    max_upload_size_bytes: int = 10 * 1024 * 1024  # 10MB

    model_config = {"env_prefix": "SPONGE_"}


settings = Settings()
