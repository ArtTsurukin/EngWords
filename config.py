import os
from dotenv import load_dotenv

load_dotenv(".env.production")

class Config:

    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN")
        self.database_url = os.getenv("DATABASE_URL")

        if not self.bot_token:
            raise ValueError("Токен не установлен")
        if not self.database_url:
            raise ValueError("БД не установлена")


config = Config()
