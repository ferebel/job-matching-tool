from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.services.scraper import run_scraper_and_store_jobs
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ScraperTriggerRequest(BaseModel):
    job_title: str = "python developer"
    location: str = "london"

@router.post("/trigger-scraper/", response_model=dict)
async def trigger_scraper_endpoint(
    request_data: ScraperTriggerRequest,
    db: Session = Depends(get_db)
):
    """
    Triggers the job scraper for the given job title and location.
    Stores scraped jobs in the database and returns a summary.
    """
    logger.info(f"Received request to trigger scraper for: Job Title='{request_data.job_title}', Location='{request_data.location}'")
    try:
        summary = run_scraper_and_store_jobs(
            db=db, 
            job_title_query=request_data.job_title, 
            location_query=request_data.location
        )
        return summary
    except Exception as e:
        logger.error(f"Error during scraper trigger for '{request_data.job_title}' in '{request_data.location}': {e}", exc_info=True)
        # Consider more specific error codes based on the type of exception
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while running the scraper: {str(e)}")

# Example of how to add more specific error handling if needed:
# except requests.exceptions.RequestException as req_err:
#     logger.error(f"Network error during scraping: {req_err}", exc_info=True)
#     raise HTTPException(status_code=503, detail=f"A network error occurred while trying to scrape jobs: {str(req_err)}")
# except ValueError as val_err: # e.g. if some config is missing
#     logger.error(f"Configuration error: {val_err}", exc_info=True)
#     raise HTTPException(status_code=500, detail=f"A configuration error occurred: {str(val_err)}")
