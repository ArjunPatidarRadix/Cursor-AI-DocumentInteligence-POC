from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from beanie import Document


class DocumentModel(Document):
    file_name: str
    file_path: str
    file_size: int
    file_text_content: str
    file_extracted_details: Dict[str, str] = Field(default_factory=dict)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "documents"


class DocumentResponse(BaseModel):
    id: str
    file_name: str
    file_size: int
    uploaded_at: datetime
