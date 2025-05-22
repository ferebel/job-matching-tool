from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.ai_matcher import match_jobs_for_claimant
from app.models.matched_job import MatchedJobRead
from app.db import crud_claimant # For checking claimant existence
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/claimants/{claimant_id}/match-jobs/",
    response_model=List[MatchedJobRead], # Returns a list of matched job entries
    summary="Trigger AI Matching for a Claimant",
    tags=["Matching"] # Using a more specific tag for this router if needed
)
async def trigger_matching_for_claimant_endpoint(
    claimant_id: int,
    db: Session = Depends(get_db)
):
    """
    Triggers the AI job matching process for a specific claimant.
    It finds relevant job postings based on the claimant's CV and job descriptions,
    then stores these matches in the database.
    Returns a list of newly created or updated matched job entries.
    """
    logger.info(f"Received request to trigger AI job matching for claimant ID: {claimant_id}")

    # Check if claimant exists
    db_claimant = crud_claimant.get_claimant(db=db, claimant_id=claimant_id)
    if not db_claimant:
        logger.warning(f"Claimant with ID {claimant_id} not found. Cannot trigger matching.")
        raise HTTPException(status_code=404, detail="Claimant not found")

    try:
        matched_job_instances = match_jobs_for_claimant(db=db, claimant_id=claimant_id)
        
        if not matched_job_instances:
            logger.info(f"No new matches found or updated for claimant ID: {claimant_id}")
            # Returning an empty list is consistent with List[MatchedJobRead] response_model
            # Optionally, could return a 200 with a message, but this requires changing response_model.
            return [] 
            
        logger.info(f"Successfully processed matching for claimant ID: {claimant_id}. Found/Updated {len(matched_job_instances)} matches.")
        # FastAPI will convert SQLMatchedJob instances to MatchedJobRead due to orm_mode=True
        # in MatchedJobRead and its nested JobPostingRead.
        return matched_job_instances
        
    except Exception as e:
        logger.error(f"Error during AI matching for claimant ID {claimant_id}: {e}", exc_info=True)
        # Consider more specific error codes based on the type of exception
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during the matching process: {str(e)}")
