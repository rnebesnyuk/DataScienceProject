from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_url: str
    db_local_url: str
    db_user: str
    db_password: str
    db_port: str
    db_name: str
    secret_key: str
    algorithm: str

    redis_host: str
    redis_local_host: str = 'localhost'
    redis_port: int = '6379'
    redis_password: str
    redis_name: str = ''
  

    model_config = ConfigDict(extra='ignore', env_file=".env", env_file_encoding="utf-8")


settings = Settings()