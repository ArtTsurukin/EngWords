from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserWordAssociation(Base):
    __tablename__ = 'user_word_association'

    user_id = Column(BigInteger, ForeignKey('users.user_id'), primary_key=True)
    word_id = Column(Integer, ForeignKey('words.id'), primary_key=True)
    learned = Column(Boolean, default=False)

    user = relationship("User", back_populates="word_associations")
    word = relationship("Word", back_populates="user_associations")


class User(Base):
    __tablename__ = "users"
    user_id = Column(BigInteger, primary_key=True, nullable=False, unique=True)
    user_first_name = Column(String(50))

    word_associations = relationship("UserWordAssociation", back_populates="user")


class Word(Base):
    __tablename__ = "words"
    id = Column(Integer, primary_key=True, autoincrement=True)
    word_eng = Column(String(50), nullable=False)
    word_rus = Column(String(50), nullable=False)

    user_associations = relationship("UserWordAssociation", back_populates="word")
