import os
from dotenv import load_dotenv

load_dotenv(".env.production")
#load_dotenv(".env.development")


class Config:

    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN")
        self.database_url = os.getenv("DATABASE_URL")
        self.openai_token = os.getenv("OPENAI_API_KEY")

        if not self.bot_token:
            raise ValueError("Токен не установлен")
        if not self.database_url:
            raise ValueError("БД не установлена")


config_bot = Config()