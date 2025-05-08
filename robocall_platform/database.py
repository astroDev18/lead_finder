# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment variable or use SQLite by default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=True if os.getenv("DEBUG", "False").lower() == "true" else False,
    pool_pre_ping=True
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
