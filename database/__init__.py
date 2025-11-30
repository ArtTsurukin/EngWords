# Create DB
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import dictionary
from config import DATABASE_URL
from database.models import Base, Word

engine = create_engine(DATABASE_URL)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def create_word_dict(all_word_list):
    session = Session()
    session.query(Word).delete(synchronize_session="fetch") # удаляем данные из таблицы
    session.add_all(all_word_list)
    session.commit()
    session.close()
    return "dictionary created"

create_word_dict(all_word_list=dictionary.all_words)

