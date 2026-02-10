from pydantic import computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from dotenv import load_dotenv


load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    IS_PROD: bool

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    ECHO: bool

    CORS_ORIGINS: list[str]
    CORS_METHODS: list[str]
    CORS_HEADERS: list[str]

    RABBITMQ_URL: str

    @computed_field
    @property
    def POSTGRES_URL_ASYNC(self) -> MultiHostUrl:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            path=self.DB_NAME,
        )


settings = Settings()
