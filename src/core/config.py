import os
from logging import config as logging_config
from pydantic import BaseSettings

from src.core.logger import LOGGING

logging_config.dictConfig(LOGGING)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE_PATH = os.path.join(BASE_DIR, '.env')


class AppSettings(BaseSettings):
    api_base_url: str
    user_token: str
    db_name: str
    pg_db_name: str
    pg_user: str
    pg_password: str
    pg_host: str
    class Config:
        env_file = ENV_FILE_PATH


app_settings = AppSettings()
