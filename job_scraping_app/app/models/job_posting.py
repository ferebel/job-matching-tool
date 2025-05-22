from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Date
from app.db.base_class import Base
from datetime import datetime

class SQLJobPosting(Base):
    __tablename__ = "job_postings" # Matches the table name in schema.sql

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    company_name = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    job_url = Column(String(2048), unique=True, index=True, nullable=False)
    source_website = Column(String(255), nullable=True)
    date_scraped = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_posted = Column(Date, nullable=True) # Changed to Date as per schema.sql
    is_active = Column(Boolean, default=True)

# Pydantic models for JobPostings would go here if needed for API interaction,
# similar to how they are defined in claimant.py. For this subtask,
# only the SQLAlchemy model is explicitly required for job_posting.py.

# Example Pydantic models (Optional for this step, but good for consistency):
from typing import Optional
from pydantic import BaseModel, HttpUrl
import datetime as dt # Alias to avoid conflict with sqlalchemy.DateTime

class JobPostingBase(BaseModel):
    title: str
    company_name: Optional[str] = None
    location: Optional[str] = None
    description: str # For Pydantic, this will be the full description if available
    job_url: HttpUrl
    source_website: Optional[str] = None
    date_posted: Optional[dt.date] = None 
    is_active: bool = True

class JobPostingCreate(JobPostingBase):
    pass

class JobPostingRead(JobPostingBase):
    id: int
    date_scraped: dt.datetime # Use aliased datetime

    class Config:
        orm_mode = True
