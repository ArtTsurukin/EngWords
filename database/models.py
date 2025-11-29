from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True)
    user_first_name = Column(String(50))
    learned_words = Column(Integer)
    unlearned_words = Column(Integer)


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    word_eng = Column(String(50), nullable=False)
    word_rus = Column(String(50), nullable=False)