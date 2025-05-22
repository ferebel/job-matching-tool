from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import crud_claimant
from app.models.claimant import (
    ClaimantCreate, ClaimantRead, ClaimantUpdate, # Added ClaimantUpdate
    ClaimantDocumentCreate, ClaimantDocumentRead,
    SQLClaimant, SQLClaimantDocument # SQLAlchemy models also imported for type hinting if needed
)
from app.services.document_parser import extract_text_from_document
import logging # For logging file processing

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ClaimantRead, status_code=201)
async def create_new_claimant(
    claimant_in: ClaimantCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new claimant.
    """
    db_claimant = crud_claimant.create_claimant(db=db, claimant=claimant_in)
    # FastAPI will convert SQLClaimant to ClaimantRead due to orm_mode=True
    return db_claimant 

@router.get("/{claimant_id}", response_model=ClaimantRead)
async def read_claimant(
    claimant_id: int, 
    db: Session = Depends(get_db)
):
    """
    Get a claimant by their ID.
    """
    db_claimant = crud_claimant.get_claimant(db=db, claimant_id=claimant_id)
    if db_claimant is None:
        raise HTTPException(status_code=404, detail="Claimant not found")
    return db_claimant

@router.post("/{claimant_id}/documents/", response_model=ClaimantDocumentRead)
async def upload_claimant_document(
    claimant_id: int,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document for a specific claimant.
    The document_type is passed as a form field.
    Text is extracted from the document.
    """
    # 1. Check if claimant exists
    db_claimant = crud_claimant.get_claimant(db=db, claimant_id=claimant_id)
    if db_claimant is None:
        logger.warning(f"Attempt to upload document for non-existent claimant ID: {claimant_id}")
        raise HTTPException(status_code=404, detail="Claimant not found for document upload")

    # 2. File Handling and Text Extraction
    try:
        file_content = await file.read()
        # It's good practice to reset the file pointer if the content needs to be read again
        # (e.g., for saving to disk, which we are currently simulating with file.filename)
        await file.seek(0) 
    except Exception as e:
        logger.error(f"Error reading uploaded file for claimant {claimant_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error reading uploaded file.")

    # Placeholder for file_path (in a real app, save the file and get its actual path)
    # For now, using file.filename as a stand-in for where the file *might* be stored.
    simulated_file_path = f"uploads/claimant_{claimant_id}/{file.filename}" 
    logger.info(f"Simulating file path: {simulated_file_path} for claimant {claimant_id}")

    extracted_text = extract_text_from_document(
        file_path=file.filename, # Using original filename for identification in parser
        file_content=file_content, 
        mime_type=file.content_type
    )
    logger.info(f"Text extraction complete for file '{file.filename}', claimant {claimant_id}. Extracted length: {len(extracted_text)}")

    # 3. Create the document metadata object using Pydantic model
    doc_create = ClaimantDocumentCreate(document_type=document_type)
    
    # 4. Call the CRUD function
    try:
        db_document = crud_claimant.add_claimant_document(
            db=db, 
            doc_create=doc_create, 
            claimant_id=claimant_id, 
            file_path=simulated_file_path, # Using simulated path
            raw_text=extracted_text
        )
    except Exception as e:
        # This could be a database error or other unexpected issue
        logger.error(f"Error adding document to DB for claimant {claimant_id}, file '{file.filename}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not save document information to the database.")

    # FastAPI will convert SQLClaimantDocument to ClaimantDocumentRead
    return db_document

@router.put("/{claimant_id}", response_model=ClaimantRead)
async def update_existing_claimant(
    claimant_id: int,
    claimant_in: ClaimantUpdate, # Use the new Pydantic model for updates
    db: Session = Depends(get_db)
):
    """
    Update an existing claimant.
    Allows partial updates for fields defined in ClaimantUpdate.
    """
    logger.info(f"Received request to update claimant ID: {claimant_id}")
    
    # Check if claimant exists (optional here, as crud_claimant.update_claimant will also check)
    # existing_claimant = crud_claimant.get_claimant(db=db, claimant_id=claimant_id)
    # if not existing_claimant:
    #     logger.warning(f"Update failed: Claimant with ID {claimant_id} not found.")
    #     raise HTTPException(status_code=404, detail="Claimant not found")

    updated_claimant = crud_claimant.update_claimant(
        db=db, claimant_id=claimant_id, claimant_update=claimant_in
    )
    
    if updated_claimant is None:
        logger.warning(f"Update operation returned None for claimant ID: {claimant_id} (likely not found).")
        # This case should be hit if get_claimant inside update_claimant returns None
        raise HTTPException(status_code=404, detail="Claimant not found for update")

    logger.info(f"Successfully updated claimant ID: {claimant_id}")
    # FastAPI will convert the returned SQLClaimant to ClaimantRead
    return updated_claimant
