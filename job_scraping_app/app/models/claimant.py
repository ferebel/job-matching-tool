from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

# SQLAlchemy specific imports
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB # For PostgreSQL specific JSON type
from sqlalchemy.orm import relationship
from app.db.base_class import Base # Import Base from your setup

# --- SQLAlchemy Models ---

class SQLClaimant(Base):
    __tablename__ = "claimants" # Matches the table name in schema.sql

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    target_location = Column(String, nullable=True) # New field
    search_keywords = Column(Text, nullable=True) # New field (stores comma-separated string or JSON string)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    documents = relationship("SQLClaimantDocument", back_populates="claimant")

class SQLClaimantDocument(Base):
    __tablename__ = "claimant_documents" # Matches the table name in schema.sql

    id = Column(Integer, primary_key=True, index=True)
    claimant_id = Column(Integer, ForeignKey("claimants.id"), nullable=False) # Corrected ForeignKey
    document_type = Column(String(50), nullable=False)
    file_path = Column(String(512), nullable=True)
    raw_text_content = Column(Text, nullable=True)
    parsed_entities = Column(JSONB, nullable=True) # Using JSONB for PostgreSQL
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    claimant = relationship("SQLClaimant", back_populates="documents")


# --- Pydantic Models (for API interaction) ---
# These can remain largely the same but ensure they align with your API needs.
# orm_mode = True in Config helps Pydantic work with SQLAlchemy objects.

class ClaimantBase(BaseModel):
    name: str
    email: EmailStr
    phone_number: Optional[str] = None
    notes: Optional[str] = None
    target_location: Optional[str] = None
    search_keywords: Optional[str] = None # Can be comma-separated string

class ClaimantCreate(ClaimantBase):
    pass

class ClaimantRead(ClaimantBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ClaimantUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None # Assuming EmailStr can be Optional if needed, or use str
    phone_number: Optional[str] = None
    notes: Optional[str] = None
    target_location: Optional[str] = None
    search_keywords: Optional[str] = None

class ClaimantDocumentBase(BaseModel):
    document_type: str
    # file_path might not be directly settable by client on creation
    # raw_text_content and parsed_entities are usually server-set

class ClaimantDocumentCreate(ClaimantDocumentBase):
    # Used when creating a document, client might only provide type,
    # file itself is handled via UploadFile.
    pass
    # These fields will be populated by the API endpoint/service layer
    # before calling the CRUD function.
    # file_path: Optional[str] = None # Moved to CRUD function signature
    # raw_text_content: Optional[str] = None # Moved to CRUD function signature
    # parsed_entities: Optional[dict] = None # This could be added later


class ClaimantDocumentRead(ClaimantDocumentBase):
    id: int
    claimant_id: int
    file_path: Optional[str] = None
    raw_text_content: Optional[str] = None # Text extracted by server
    parsed_entities: Optional[dict] = None # Structured data extracted by server
    uploaded_at: datetime

    class Config:
        orm_mode = True
