import os
from dotenv import load_dotenv


class Config:

    def __init__(self):
        self.env = os.getenv("APP_ENV", "production")

        self._load_env_vars()

        self.bot_token = self._get_bot_token()
        self.database_url = self._get_database_url()


    def _load_env_vars(self):
        env_file = f".env.{self.env}"
        load_dotenv(env_file)

    def _get_bot_token(self):
        return os.getenv("BOT_TOKEN")

    def _get_database_url(self):
        return os.getenv("DATABASE_URL")

config = Config()


