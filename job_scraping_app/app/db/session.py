from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Ensure DATABASE_URL is loaded and available
if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL not set in settings. Make sure your .env file is configured correctly.")

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
