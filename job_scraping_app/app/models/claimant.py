from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

class ClaimantBase(BaseModel):
    name: str
    email: EmailStr
    phone_number: Optional[str] = None
    notes: Optional[str] = None

class ClaimantCreate(ClaimantBase):
    pass

class ClaimantRead(ClaimantBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ClaimantDocumentBase(BaseModel):
    document_type: str

class ClaimantDocumentCreate(ClaimantDocumentBase):
    pass

class ClaimantDocumentRead(ClaimantDocumentBase):
    id: int
    claimant_id: int
    file_path: Optional[str] = None
    raw_text_content: Optional[str] = None
    uploaded_at: datetime

    class Config:
        orm_mode = True
