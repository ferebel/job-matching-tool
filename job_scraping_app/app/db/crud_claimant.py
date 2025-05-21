from typing import Any, Optional
from fastapi import UploadFile
from app.models.claimant import ClaimantCreate, ClaimantRead, ClaimantDocumentRead
from datetime import datetime
import os
# import shutil # No longer using shutil for mock
from app.services.document_parser import extract_text_from_document
import logging

logger = logging.getLogger(__name__)

# Mock database (in-memory dictionary)
mock_db_claimants = {}
mock_db_documents = {} # Stores lists of documents per claimant_id
next_claimant_id = 1
next_document_id = 1

def create_claimant(db: Any, claimant: ClaimantCreate) -> ClaimantRead:
    global next_claimant_id
    now = datetime.utcnow()
    new_claimant = ClaimantRead(
        id=next_claimant_id,
        created_at=now,
        updated_at=now,
        **claimant.dict()
    )
    mock_db_claimants[next_claimant_id] = new_claimant
    next_claimant_id += 1
    logger.info(f"Created claimant: {new_claimant.id} - {new_claimant.name}")
    return new_claimant

def get_claimant(db: Any, claimant_id: int) -> Optional[ClaimantRead]:
    claimant = mock_db_claimants.get(claimant_id)
    if claimant:
        logger.info(f"Retrieved claimant: {claimant_id}")
    else:
        logger.info(f"Claimant not found: {claimant_id}")
    return claimant

async def add_claimant_document(db: Any, claimant_id: int, file: UploadFile, document_type: str) -> Optional[ClaimantDocumentRead]:
    global next_document_id
    claimant = get_claimant(db, claimant_id)
    if not claimant:
        logger.warning(f"Cannot add document. Claimant not found: {claimant_id}")
        return None

    # Simulate saving the file - path generation
    # In a real app, you'd ensure the upload_dir exists and save the file securely.
    # For mock purposes, we'll just generate a path.
    upload_dir = f"uploads/claimant_{claimant_id}"
    # os.makedirs(upload_dir, exist_ok=True) # Not creating dir in mock
    file_path = os.path.join(upload_dir, file.filename)
    logger.info(f"Simulating file save for '{file.filename}' to path '{file_path}' for claimant {claimant_id}.")

    # Read file content for text extraction
    file_content = await file.read()
    await file.seek(0) # Reset file pointer if it needs to be read again (e.g. for actual saving)

    logger.info(f"Attempting to extract text from document: {file.filename}, MIME: {file.content_type}")
    extracted_text = extract_text_from_document(
        file_path=file.filename, 
        file_content=file_content, 
        mime_type=file.content_type
    )
    
    # For mock, we might just store a snippet or confirmation
    raw_text_content_for_model = f"Text extracted (length: {len(extracted_text)})." 
    if not extracted_text:
        raw_text_content_for_model = "Text extraction failed or document was empty."
        logger.warning(f"Text extraction yielded no content for: {file.filename}")


    now = datetime.utcnow()
    new_document = ClaimantDocumentRead(
        id=next_document_id,
        claimant_id=claimant_id,
        document_type=document_type,
        file_path=file_path, # Store the simulated path
        raw_text_content=raw_text_content_for_model, # Add extracted text info
        uploaded_at=now
    )
    
    if claimant_id not in mock_db_documents:
        mock_db_documents[claimant_id] = []
    mock_db_documents[claimant_id].append(new_document)
    next_document_id += 1
    logger.info(f"Added document {new_document.id} ({new_document.document_type}) for claimant {claimant_id}. Path: {new_document.file_path}")
    return new_document
