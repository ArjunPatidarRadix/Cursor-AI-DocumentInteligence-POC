from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from ..database.models import DocumentModel, DocumentResponse
from ..config.settings import get_settings
from ..services.qa_service import qa_service
from ..services.document_service import document_service
from pydantic import BaseModel
from pathlib import Path
from typing import List

router = APIRouter()
settings = get_settings()


class QuestionRequest(BaseModel):
    question: str


class QuestionResponse(BaseModel):
    answer: str
    confidence: float
    success: bool


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    return await document_service.upload_document(file)


@router.get("/list", response_model=List[DocumentResponse])
async def list_documents():
    return await document_service.list_documents()


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


@router.post("/{document_id}/ask", response_model=QuestionResponse)
async def ask_question(document_id: str, request: QuestionRequest):
    try:
        # Get the document
        document = await document_service.get_document(document_id)
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

        # Get the answer
        result = qa_service.answer_question(request.question, document_text)

        return QuestionResponse(
            answer=result["answer"],
            confidence=result["confidence"],
            success=result["success"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
