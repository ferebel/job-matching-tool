import pytest
from sqlalchemy.orm import Session
from app.db import crud_jobs
from app.models.job_posting import SQLJobPosting # SQLAlchemy model
from datetime import date, datetime

# Test data
SAMPLE_JOB_DATA_1 = {
    "title": "Python Developer",
    "company_name": "Tech Corp",
    "location": "London",
    "description_snippet": "Develop cool Python stuff.",
    "job_url": "https://www.example.com/job/python-dev-1",
    "source_website": "Example.com",
    "date_posted": date(2023, 1, 15) 
}

SAMPLE_JOB_DATA_2 = {
    "title": "Software Engineer",
    "company_name": "Innovate LLC",
    "location": "Remote",
    "description_snippet": "Work on cutting-edge software.",
    "job_url": "https://www.example.com/job/software-eng-2",
    "source_website": "Example.com",
    "date_posted": date(2023, 1, 20)
}

SAMPLE_JOB_DATA_DUPLICATE_URL = {
    "title": "Python Developer (Updated)", # Different title
    "company_name": "Tech Corp",
    "location": "London",
    "description_snippet": "Develop cool Python stuff, now updated.",
    "job_url": "https://www.example.com/job/python-dev-1", # Same URL as SAMPLE_JOB_DATA_1
    "source_website": "Example.com",
    "date_posted": date(2023, 1, 18) # Different date
}


def test_create_job_posting_new(test_db_session: Session):
    job, created = crud_jobs.create_job_posting(db=test_db_session, job_data=SAMPLE_JOB_DATA_1)
    
    assert created is True
    assert job is not None
    assert job.title == SAMPLE_JOB_DATA_1["title"]
    assert job.job_url == SAMPLE_JOB_DATA_1["job_url"]
    assert job.company_name == SAMPLE_JOB_DATA_1["company_name"]
    assert job.location == SAMPLE_JOB_DATA_1["location"]
    assert job.description == SAMPLE_JOB_DATA_1["description_snippet"]
    assert job.source_website == SAMPLE_JOB_DATA_1["source_website"]
    assert job.date_posted == SAMPLE_JOB_DATA_1["date_posted"]
    assert job.id is not None
    assert isinstance(job.date_scraped, datetime)
    assert job.is_active is True

    # Verify it's in the DB
    db_job = test_db_session.query(SQLJobPosting).filter(SQLJobPosting.id == job.id).first()
    assert db_job is not None
    assert db_job.job_url == SAMPLE_JOB_DATA_1["job_url"]

def test_create_job_posting_existing_url(test_db_session: Session):
    # First, create the initial job
    job1, created1 = crud_jobs.create_job_posting(db=test_db_session, job_data=SAMPLE_JOB_DATA_1)
    assert created1 is True
    assert job1 is not None
    
    # Attempt to create a job with the same URL
    job2, created2 = crud_jobs.create_job_posting(db=test_db_session, job_data=SAMPLE_JOB_DATA_DUPLICATE_URL)
    
    assert created2 is False # Should indicate existing job was returned
    assert job2 is not None
    assert job2.id == job1.id # Should be the same job ID
    assert job2.job_url == SAMPLE_JOB_DATA_1["job_url"] 
    # Check that the original data is preserved (or updated, depending on policy, current policy is to preserve)
    assert job2.title == SAMPLE_JOB_DATA_1["title"] # Original title
    assert job2.date_posted == SAMPLE_JOB_DATA_1["date_posted"] # Original date

def test_get_job_posting_by_url(test_db_session: Session):
    # Create a job
    crud_jobs.create_job_posting(db=test_db_session, job_data=SAMPLE_JOB_DATA_1)
    
    # Retrieve it by URL
    retrieved_job = crud_jobs.get_job_posting_by_url(db=test_db_session, job_url=SAMPLE_JOB_DATA_1["job_url"])
    assert retrieved_job is not None
    assert retrieved_job.title == SAMPLE_JOB_DATA_1["title"]
    
    # Test for non-existent URL
    non_existent_job = crud_jobs.get_job_posting_by_url(db=test_db_session, job_url="https://www.example.com/job/non-existent")
    assert non_existent_job is None

def test_get_job_postings(test_db_session: Session):
    # Clear table or ensure it's clean if tests run in sequence and affect each other
    # For now, assuming test_db_session provides a clean start or handles this.
    # If not, add cleanup: test_db_session.query(SQLJobPosting).delete(); test_db_session.commit()
    
    # Create a couple of jobs
    crud_jobs.create_job_posting(db=test_db_session, job_data=SAMPLE_JOB_DATA_1)
    crud_jobs.create_job_posting(db=test_db_session, job_data=SAMPLE_JOB_DATA_2)
    
    # Test basic retrieval
    all_jobs = crud_jobs.get_job_postings(db=test_db_session)
    # Check if at least 2 jobs are found (could be more if other tests ran before without full cleanup)
    # For more precise count, ensure clean state or filter by specific IDs created here.
    # For now, simple check:
    assert len(all_jobs) >= 2 
    
    # Test with limit
    limited_jobs = crud_jobs.get_job_postings(db=test_db_session, limit=1)
    assert len(limited_jobs) == 1
    
    # Test with skip and limit
    # Create one more job to ensure there are at least 2 for this test part
    job_urls_in_db = {job.job_url for job in all_jobs}
    if SAMPLE_JOB_DATA_1["job_url"] not in job_urls_in_db:
         crud_jobs.create_job_posting(db=test_db_session, job_data=SAMPLE_JOB_DATA_1)
    if SAMPLE_JOB_DATA_2["job_url"] not in job_urls_in_db:
         crud_jobs.create_job_posting(db=test_db_session, job_data=SAMPLE_JOB_DATA_2)
    
    # Re-fetch all jobs to get current count and order
    all_jobs = test_db_session.query(SQLJobPosting).order_by(SQLJobPosting.id).all()
    if len(all_jobs) >= 2:
        skipped_job = crud_jobs.get_job_postings(db=test_db_session, skip=1, limit=1)
        assert len(skipped_job) == 1
        # Ensure the skipped job is different from the first one if order is predictable
        # This depends on default ordering (e.g., by ID)
        first_job_by_id = all_jobs[0]
        second_job_by_id = all_jobs[1]
        
        first_retrieved_limit1 = crud_jobs.get_job_postings(db=test_db_session, limit=1)[0]
        assert first_retrieved_limit1.id == first_job_by_id.id
        
        if skipped_job: # Ensure list is not empty
             assert skipped_job[0].id == second_job_by_id.id
    else:
        pytest.skip("Not enough jobs in DB to test skip reliably without more control over DB state.")

# Test date_posted handling (if it were a string, which it's not in current SAMPLE_JOB_DATA)
# def test_create_job_posting_with_string_date(test_db_session: Session):
#     job_data_str_date = {
#         **SAMPLE_JOB_DATA_1,
#         "job_url": "https://www.example.com/job/python-dev-date-str", # Unique URL
#         "date_posted": "2023-01-25" 
#     }
#     # If create_job_posting handled string-to-date conversion:
#     # job, created = crud_jobs.create_job_posting(db=test_db_session, job_data=job_data_str_date)
#     # assert created is True
#     # assert isinstance(job.date_posted, date)
#     # assert job.date_posted == date(2023, 1, 25)
#     pass # Current implementation expects date object or None.
