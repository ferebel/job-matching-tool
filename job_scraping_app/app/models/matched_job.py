from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, UniqueConstraint
# from sqlalchemy.orm import relationship # Moved below to avoid import before SQLClaimant/SQLJobPosting
from app.db.base_class import Base

# Forward declaration for relationships if models are in different files and there are circular dependencies.
# However, for Pydantic models, we import them directly.
from app.models.job_posting import JobPostingRead # For Pydantic schema
# For SQLAlchemy relationships, use string references to avoid circular imports at module load time
# or ensure models are loaded in correct order if using direct class references.

class SQLMatchedJob(Base):
    __tablename__ = "matched_jobs"

    id = Column(Integer, primary_key=True, index=True)
    claimant_id = Column(Integer, ForeignKey("claimants.id"), nullable=False) # SQLClaimant table name is 'claimants'
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    match_score = Column(Float, nullable=True)
    status = Column(String(50), default='new', nullable=False) # Max length for String
    match_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes_for_advisor = Column(Text, nullable=True)

    # Define relationships using string names of the classes
    # This avoids direct import issues at module load time if SQLClaimant/SQLJobPosting are in other files.
    # The back_populates argument should match the relationship attribute name in the other model.
    # Assuming SQLClaimant has a 'matched_jobs_collection' relationship and SQLJobPosting has one too.
    # If those are not defined yet, back_populates can be omitted or defined later.
    from sqlalchemy.orm import relationship # Moved here
    claimant = relationship("SQLClaimant") #, back_populates="matched_jobs_collection") # Need to define this in SQLClaimant
    job_posting = relationship("SQLJobPosting") #, back_populates="matched_jobs_collection") # Need to define this in SQLJobPosting

    __table_args__ = (UniqueConstraint('claimant_id', 'job_posting_id', name='uq_claimant_job_match'),)


class MatchedJobBase(BaseModel):
    claimant_id: int
    job_posting_id: int
    match_score: Optional[float] = None
    status: Optional[str] = 'new'
    notes_for_advisor: Optional[str] = None

class MatchedJobCreate(MatchedJobBase):
    pass

class MatchedJobRead(MatchedJobBase):
    id: int
    match_date: datetime
    job_posting: JobPostingRead # Embeds JobPosting details

    class Config:
        orm_mode = True

# To complete relationships, you would add to SQLClaimant in claimant.py:
# from app.models.matched_job import SQLMatchedJob # At top of file if not causing circularity
# matched_jobs_collection = relationship("SQLMatchedJob", back_populates="claimant")
#
# And to SQLJobPosting in job_posting.py:
# from app.models.matched_job import SQLMatchedJob
# matched_jobs_collection = relationship("SQLMatchedJob", back_populates="job_posting")
# For now, these back_populates are commented out in SQLMatchedJob to avoid errors
# if the corresponding relationships are not yet defined on SQLClaimant and SQLJobPosting.
# For the relationship to work correctly from MatchedJob's side without back_populates,
# it's fine, but back_populates is good for bidirectional navigation.

# Correcting ForeignKey references if SQLClaimant is defined with a different tablename
# The current SQLClaimant model uses __tablename__ = "claimants"
# So, ForeignKey("claimants.id") is correct.
# SQLJobPosting uses __tablename__ = "job_postings"
# So, ForeignKey("job_postings.id") is correct.
