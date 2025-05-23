from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Ensure DATABASE_URL is loaded and available
if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL not set in settings. Make sure your .env file is configured correctly.")

# Ensure the DATABASE_URL uses the 'postgresql://' scheme
db_url = settings.DATABASE_URL
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url, pool_pre_ping=True) # Preserved pool_pre_ping
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
