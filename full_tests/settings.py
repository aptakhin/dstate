from pydantic import BaseSettings


class Settings(BaseSettings):
    mongodb_dsn: str

    class Config:
        env_file = '.env'
