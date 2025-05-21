from typing import Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from app.models.claimant import ClaimantCreate, ClaimantRead, ClaimantDocumentRead
from app.db import crud_claimant  # Assuming crud_claimant will be in app.db

router = APIRouter()

# Placeholder for DB session dependency, not used yet but good for structure
def get_db():
    # In a real app, this would return a database session
    return None

@router.post("/", response_model=ClaimantRead, status_code=201)
async def create_new_claimant(claimant: ClaimantCreate, db: Any = Depends(get_db)):
    """
    Create a new claimant.
    """
    return crud_claimant.create_claimant(db=db, claimant=claimant)

@router.get("/{claimant_id}", response_model=ClaimantRead)
async def read_claimant(claimant_id: int, db: Any = Depends(get_db)):
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
    db: Any = Depends(get_db)
):
    """
    Upload a document for a specific claimant.
    The document_type is passed as a form field.
    """
    db_claimant = crud_claimant.get_claimant(db=db, claimant_id=claimant_id)
    if db_claimant is None:
        raise HTTPException(status_code=404, detail="Claimant not found for document upload")

    document = crud_claimant.add_claimant_document(
        db=db, claimant_id=claimant_id, file=file, document_type=document_type
    )
    if document is None:
        # This case should ideally be handled by the check above or within add_claimant_document
        raise HTTPException(status_code=400, detail="Document could not be processed")
    return document
