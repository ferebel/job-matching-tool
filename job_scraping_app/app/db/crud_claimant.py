from typing import Optional
from sqlalchemy.orm import Session
from app.models.claimant import SQLClaimant, SQLClaimantDocument, ClaimantCreate, ClaimantDocumentCreate # Pydantic models for creation
# Note: ClaimantRead and ClaimantDocumentRead are used by API, not directly returned by CRUD now
# from app.services.document_parser import extract_text_from_document # No longer in CRUD
import logging
# import os # For path manipulation if saving files, not directly in CRUD now

logger = logging.getLogger(__name__)

# No more mock DB or global counters
# mock_db_claimants = {}
# mock_db_documents = {} 
# next_claimant_id = 1
# next_document_id = 1

def create_claimant(db: Session, claimant: ClaimantCreate) -> SQLClaimant:
    """
    Create a new claimant in the database.
    """
    db_claimant = SQLClaimant(
        name=claimant.name,
        email=claimant.email,
        phone_number=claimant.phone_number,
        notes=claimant.notes,
        target_location=claimant.target_location, # Added
        search_keywords=claimant.search_keywords  # Added
        # created_at and updated_at are handled by default/onupdate in SQLClaimant model
    )
    db.add(db_claimant)
    db.commit()
    db.refresh(db_claimant)
    logger.info(f"Created claimant with ID: {db_claimant.id} - Name: {db_claimant.name}")
    return db_claimant

def get_claimant(db: Session, claimant_id: int) -> Optional[SQLClaimant]:
    """
    Get a claimant by their ID from the database.
    """
    claimant = db.query(SQLClaimant).filter(SQLClaimant.id == claimant_id).first()
    if claimant:
        logger.info(f"Retrieved claimant with ID: {claimant_id}")
    else:
        logger.info(f"Claimant with ID: {claimant_id} not found.")
    return claimant

def add_claimant_document(
    db: Session, 
    doc_create: ClaimantDocumentCreate, # Pydantic model containing document_type
    claimant_id: int, 
    file_path: Optional[str], 
    raw_text: Optional[str]
) -> SQLClaimantDocument:
    """
    Add a new document for a claimant to the database.
    The API layer is responsible for providing claimant_id, file_path, and raw_text.
    """
    
    db_document = SQLClaimantDocument(
        claimant_id=claimant_id,
        document_type=doc_create.document_type,
        file_path=file_path,
        raw_text_content=raw_text
        # parsed_entities can be added here if it's part of initial creation
        # uploaded_at is handled by default in SQLClaimantDocument model
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    logger.info(f"Added document ID: {db_document.id} ({db_document.document_type}) for claimant ID: {claimant_id}. Path: {db_document.file_path}")
    return db_document


def update_claimant(db: Session, claimant_id: int, claimant_update: "ClaimantUpdate") -> Optional[SQLClaimant]: # ClaimantUpdate from app.models.claimant
    """
    Update an existing claimant in the database.
    """
    db_claimant = get_claimant(db, claimant_id)
    if not db_claimant:
        logger.warning(f"Claimant with ID {claimant_id} not found for update.")
        return None

    update_data = claimant_update.dict(exclude_unset=True) # Get only fields that were actually set
    
    updated_fields_count = 0
    for field, value in update_data.items():
        if hasattr(db_claimant, field):
            setattr(db_claimant, field, value)
            updated_fields_count +=1
        # else:
            # logger.warning(f"Attempted to update non-existent field '{field}' on SQLClaimant.")

    if updated_fields_count > 0:
        # db_claimant.updated_at = datetime.utcnow() # SQLAlchemy onupdate handles this
        db.commit()
        db.refresh(db_claimant)
        logger.info(f"Updated claimant with ID: {claimant_id}. {updated_fields_count} fields changed.")
    else:
        logger.info(f"No fields to update for claimant with ID: {claimant_id}.")
        
    return db_claimant
