# Create DB
import logging
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from dictionary import oxford_3000
from config import config_bot
from database.models import Base, Word

logger = logging.getLogger(__name__)
engine = create_engine(config_bot.database_url)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

#Добавляем слова в словарь после создания БД. Если в словаре уже есть слова, пропускаем
def create_word_dict():
    session = Session()
    if session.query(func.count(Word.id)).scalar() < 1:
        session.add_all(oxford_3000)
        session.commit()
        logger.info(msg="db_created", extra={"status": "success"})
    else:
        logger.info(msg="db_exists", extra={"status": "success"})

    session.close()

create_word_dict()










