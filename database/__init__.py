# Create DB
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from dictionary import oxford_3000
from config import config
from database.models import Base, Word

engine = create_engine(config.database_url)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

#Добавляем слова в словарь после создания БД. Если в словаре уже есть слова, пропускаем
def create_word_dict():
    session = Session()
    if session.query(func.count(Word.id)).scalar() < 1:
        session.add_all(oxford_3000)
        session.commit()
        print("create DB")
    else:
        print("DB already exist")

    session.close()

create_word_dict()










