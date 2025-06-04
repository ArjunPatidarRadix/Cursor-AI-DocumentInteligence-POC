from typing import Dict, List, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from beanie import Document


class DocumentModel(Document):
    file_name: str
    file_path: str
    file_size: int
    file_text_content: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    indexing_status: str = "pending"  # pending, processing, completed, failed
    indexing_error: Optional[str] = None
    file_extracted_details: Optional[Dict[str, Any]] = None
    processing_progress: Dict[str, float] = Field(default_factory=lambda: {
        "text_extraction": 0.0,
        "classification": 0.0,
        "entity_extraction": 0.0,
        "table_extraction": 0.0,
        "summarization": 0.0,
        "rag_indexing": 0.0
    })
    processing_retries: Dict[str, int] = Field(default_factory=lambda: {
        "text_extraction": 0,
        "classification": 0,
        "entity_extraction": 0,
        "table_extraction": 0,
        "summarization": 0,
        "rag_indexing": 0
    })
    max_retries: int = 3

    class Settings:
        name = "documents"


class DocumentResponse(BaseModel):
    id: str
    file_name: str
    file_size: int
    uploaded_at: datetime
    indexing_status: str
    indexing_error: Optional[str] = None


class ChatMessage(Document):
    document_id: str
    type: str  # "question" or "answer"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence: Optional[float] = None
    success: Optional[bool] = None
    model_name: Optional[str] = None  # Store which model was used

    class Settings:
        name = "chat_messages"


class ChatMessageResponse(BaseModel):
    id: str
    document_id: str
    type: str
    content: str
    timestamp: datetime
    confidence: Optional[float]
    success: Optional[bool]
    model_name: Optional[str] = None


# Available LLM Models
ModelType = Literal[
    "roberta-base-squad2",
    "distilbert-base-cased-distilled-squad",
    "bert-large-uncased-whole-word-masking-finetuned-squad",
    "deepset/tinyroberta-squad2",
    "distilbert-base-uncased-distilled-squad",
    "deepset/minilm-uncased-squad2",
    "microsoft/deberta-v3-base-squad2"
]

class ModelInfo(BaseModel):
    id: ModelType
    name: str
    description: str
    is_default: bool = False
