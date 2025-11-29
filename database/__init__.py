# Create DB
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from database.models import Base

engine = create_engine(DATABASE_URL)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

session = Session() # экземпляр БД - использовать в логике бота