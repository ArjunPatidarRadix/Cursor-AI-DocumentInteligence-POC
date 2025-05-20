from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from ..database.models import (
    DocumentModel,
    DocumentResponse,
    ChatMessage,
    ChatMessageResponse,
    ModelType,
    ModelInfo
)
from ..config.settings import get_settings
from ..services.qa_service import qa_service
from ..services.document_service import document_service
from ..services.rag_service import rag_service
from pydantic import BaseModel
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import BackgroundTasks

router = APIRouter()
settings = get_settings()


# Available models configuration
AVAILABLE_MODELS = [
    ModelInfo(
        id="roberta-base-squad2",
        name="RoBERTa Base SQuAD2",
        description="Robust and well-balanced model for question answering",
        is_default=True
    ),
    ModelInfo(
        id="distilbert-base-cased-distilled-squad",
        name="DistilBERT Cased SQuAD",
        description="Lightweight and fast model with good accuracy",
    ),
    ModelInfo(
        id="bert-large-uncased-whole-word-masking-finetuned-squad",
        name="BERT Large SQuAD",
        description="Large model with high accuracy but slower inference",
    ),
    ModelInfo(
        id="deepset/tinyroberta-squad2",
        name="Tiny RoBERTa SQuAD2",
        description="Very lightweight model for fast inference",
    ),
    ModelInfo(
        id="distilbert-base-uncased-distilled-squad",
        name="DistilBERT Uncased SQuAD",
        description="Lightweight uncased model optimized for speed",
    ),
    ModelInfo(
        id="deepset/minilm-uncased-squad2",
        name="MiniLM SQuAD2",
        description="Compact model with good performance-speed tradeoff",
    ),
    ModelInfo(
        id="microsoft/deberta-v3-base-squad2",
        name="DeBERTa v3 SQuAD2",
        description="Advanced model with strong performance",
    ),
]


class QuestionRequest(BaseModel):
    question: str
    model_id: ModelType


class QuestionResponse(BaseModel):
    answer: str
    confidence: float
    success: bool
    model_name: str


class RAGSearchRequest(BaseModel):
    query: str
    model_id: Optional[ModelType] = None


class RAGSearchResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]


class DocumentAnalysisResponse(BaseModel):
    classification: Dict[str, Any]
    entities: Dict[str, List[Dict[str, Any]]]
    summary: Dict[str, Any]
    tables: List[Dict[str, Any]]


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a new document"""
    try:
        return await document_service.upload_document(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[DocumentResponse])
async def list_documents():
    """List all documents"""
    try:
        documents = await DocumentModel.find_all().to_list()
        return [
            DocumentResponse(
                id=str(doc.id),
                file_name=doc.file_name,
                file_size=doc.file_size,
                uploaded_at=doc.uploaded_at,
                indexing_status=doc.indexing_status,
                indexing_error=doc.indexing_error
            )
            for doc in documents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/content")
async def get_document_content(document_id: str):
    try:
        document = await document_service.get_document(document_id)
        file_path = Path(document.file_path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document file not found")

        return FileResponse(
            path=file_path,
            filename=document.file_name,
            media_type=document_service.get_content_type(document.file_name),
            content_disposition_type="inline",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[DocumentResponse])
async def search_documents(query: str = Query(..., min_length=1)):
    return await document_service.search_documents(query)


@router.get("/models", response_model=List[ModelInfo])
async def list_models():
    """List all available LLM models"""
    return AVAILABLE_MODELS


@router.post("/{document_id}/ask", response_model=QuestionResponse)
async def ask_question(document_id: str, request: QuestionRequest):
    try:
        # Get the document
        document = await DocumentModel.get(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = Path(document.file_path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document file not found")

        # Extract text from the document
        try:
            document_text = qa_service.extract_text_from_document(file_path)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error extracting text: {str(e)}"
            )

        # Get the answer using the specified model
        result = qa_service.answer_question(
            request.question,
            document_text,
            model_id=request.model_id
        )

        # Save question to chat history
        question_message = ChatMessage(
            document_id=document_id,
            type="question",
            content=request.question,
            timestamp=datetime.utcnow(),
            model_name=request.model_id
        )
        await question_message.insert()

        # Save answer to chat history
        answer_message = ChatMessage(
            document_id=document_id,
            type="answer",
            content=result["answer"],
            confidence=result["confidence"],
            success=result["success"],
            timestamp=datetime.utcnow(),
            model_name=request.model_id
        )
        await answer_message.insert()

        return QuestionResponse(
            answer=result["answer"],
            confidence=result["confidence"],
            success=result["success"],
            model_name=request.model_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/chat-history", response_model=List[ChatMessageResponse])
async def get_chat_history(document_id: str):
    try:
        # Get all chat messages for the document, sorted by timestamp
        messages = await ChatMessage.find(
            ChatMessage.document_id == document_id
        ).sort("+timestamp").to_list()
        
        return [
            ChatMessageResponse(
                id=str(msg.id),
                document_id=msg.document_id,
                type=msg.type,
                content=msg.content,
                timestamp=msg.timestamp,
                confidence=msg.confidence,
                success=msg.success,
                model_name=msg.model_name
            )
            for msg in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag-search", response_model=RAGSearchResponse)
async def rag_search(request: RAGSearchRequest):
    """Search across all documents using RAG."""
    try:
        result = await rag_service.query_documents(request.query, request.model_id)
        return RAGSearchResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/analysis", response_model=DocumentAnalysisResponse)
async def get_document_analysis(document_id: str):
    """Get document analysis results."""
    try:
        analysis = await document_service.get_document_analysis(document_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/entities")
async def get_document_entities(document_id: str):
    """Get extracted entities from document."""
    try:
        analysis = await document_service.get_document_analysis(document_id)
        print("analysis::", analysis)
        return analysis["entities"]
    except Exception as e:
        print("error::", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/summary")
async def get_document_summary(document_id: str):
    """Get document summary."""
    try:
        analysis = await document_service.get_document_analysis(document_id)
        return analysis["summary"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/tables")
async def get_document_tables(document_id: str):
    """Get extracted tables from document."""
    try:
        analysis = await document_service.get_document_analysis(document_id)
        return analysis["tables"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/classification")
async def get_document_classification(document_id: str):
    """Get document classification."""
    try:
        analysis = await document_service.get_document_analysis(document_id)
        return analysis["classification"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
