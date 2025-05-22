from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.matched_job import SQLMatchedJob, MatchedJobCreate
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_matched_job_by_claimant_and_job_posting(
    db: Session, claimant_id: int, job_posting_id: int
) -> Optional[SQLMatchedJob]:
    """
    Retrieves a specific matched job by claimant_id and job_posting_id.
    """
    return db.query(SQLMatchedJob).filter(
        SQLMatchedJob.claimant_id == claimant_id,
        SQLMatchedJob.job_posting_id == job_posting_id
    ).first()

def create_matched_job(db: Session, match: MatchedJobCreate) -> SQLMatchedJob:
    """
    Creates a new matched job or updates an existing one for the same claimant and job posting.
    """
    existing_match = get_matched_job_by_claimant_and_job_posting(
        db, claimant_id=match.claimant_id, job_posting_id=match.job_posting_id
    )

    if existing_match:
        logger.info(f"Match for Claimant ID {match.claimant_id} and Job ID {match.job_posting_id} already exists. Updating.")
        existing_match.match_score = match.match_score
        existing_match.status = match.status
        existing_match.notes_for_advisor = match.notes_for_advisor
        existing_match.match_date = datetime.utcnow() # Update match_date on modification
        db_match = existing_match
    else:
        logger.info(f"Creating new match for Claimant ID {match.claimant_id} and Job ID {match.job_posting_id}.")
        db_match = SQLMatchedJob(
            claimant_id=match.claimant_id,
            job_posting_id=match.job_posting_id,
            match_score=match.match_score,
            status=match.status,
            notes_for_advisor=match.notes_for_advisor
            # match_date will use default=datetime.utcnow
        )
        db.add(db_match)
    
    db.commit()
    db.refresh(db_match)
    return db_match

def get_matched_jobs_for_claimant(
    db: Session, claimant_id: int, skip: int = 0, limit: int = 100
) -> List[SQLMatchedJob]:
    """
    Retrieves a list of matched jobs for a specific claimant.
    """
    return db.query(SQLMatchedJob).filter(SQLMatchedJob.claimant_id == claimant_id).offset(skip).limit(limit).all()

def get_all_matched_jobs( # Added for potential admin/overview purposes
    db: Session, skip: int = 0, limit: int = 100
) -> List[SQLMatchedJob]:
    """
    Retrieves all matched jobs.
    """
    return db.query(SQLMatchedJob).offset(skip).limit(limit).all()
