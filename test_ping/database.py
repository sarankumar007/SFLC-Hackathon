from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, 'secrets.env')
load_dotenv(dotenv_path)


DATABASE_URL = os.getenv("DATABASE_URL")
print(f"DATABASE_URL is: {DATABASE_URL}")  # Debug print

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set or empty!")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
