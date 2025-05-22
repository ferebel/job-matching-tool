from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.job_posting import SQLJobPosting
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_job_posting_by_url(db: Session, job_url: str) -> Optional[SQLJobPosting]:
    """
    Get a job posting by its URL.
    """
    return db.query(SQLJobPosting).filter(SQLJobPosting.job_url == job_url).first()

def create_job_posting(db: Session, job_data: dict) -> tuple[SQLJobPosting, bool]:
    """
    Create a new job posting in the database.
    If a job with the same URL already exists, it returns the existing job and False.
    Otherwise, it creates the job and returns it with True.
    """
    existing_job = get_job_posting_by_url(db, job_data["job_url"])
    if existing_job:
        logger.info(f"Job posting with URL {job_data['job_url']} already exists. Returning existing.")
        # Optionally, update the existing job if needed, e.g., date_scraped or is_active
        # existing_job.date_scraped = datetime.utcnow() # Consider if this should mark it as "found again"
        # existing_job.is_active = True 
        # db.commit()
        # db.refresh(existing_job)
        return existing_job, False # False indicates an existing job was returned

    # Convert date_posted from string to date object if necessary
    # For now, assuming job_data["date_posted"] is already a date object or None
    # If it's a string, it should be parsed:
    # if job_data.get("date_posted") and isinstance(job_data["date_posted"], str):
    #     try:
    #         job_data["date_posted"] = datetime.strptime(job_data["date_posted"], '%Y-%m-%d').date()
    #     except ValueError:
    #         logger.warning(f"Could not parse date_posted string: {job_data['date_posted']}. Setting to None.")
    #         job_data["date_posted"] = None
            
    db_job = SQLJobPosting(
        title=job_data.get("title"),
        company_name=job_data.get("company_name"),
        location=job_data.get("location"),
        description=job_data.get("description_snippet"), # Using description_snippet as description
        job_url=job_data.get("job_url"),
        source_website=job_data.get("source_website"),
        date_posted=job_data.get("date_posted"), # Ensure this is a date object or None
        # date_scraped and is_active have defaults in the model
    )
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    logger.info(f"Created new job posting with ID: {db_job.id} - URL: {db_job.job_url}")
    return db_job, True # True indicates a new job was created

def get_job_postings(db: Session, skip: int = 0, limit: int = 100) -> List[SQLJobPosting]:
    """
    Retrieve a list of job postings.
    """
    return db.query(SQLJobPosting).offset(skip).limit(limit).all()

# Example Pydantic model for JobPostingCreate (Optional, as dict is used)
# from pydantic import BaseModel, HttpUrl
# from typing import Optional
# from datetime import date

# class JobPostingCreateSchema(BaseModel):
#     title: str
#     job_url: HttpUrl # Using HttpUrl for validation
#     company_name: Optional[str] = None
#     location: Optional[str] = None
#     description_snippet: Optional[str] = None
#     source_website: Optional[str] = None
#     date_posted: Optional[date] = None

    # class Config:
    #     orm_mode = True # Not needed for creation schema unless it's also a read schema
