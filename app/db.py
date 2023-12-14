from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

Session = None

if DATABASE_URL is not None:
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
else:
    raise ValueError("DATABASE_URL environment variable not set")
