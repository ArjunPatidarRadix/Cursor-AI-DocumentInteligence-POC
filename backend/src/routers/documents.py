from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from ..database.models import DocumentModel, DocumentResponse
from ..config.settings import get_settings
from ..services.qa_service import qa_service
from pydantic import BaseModel
import shutil
from pathlib import Path
from typing import List
import os
import re

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
    try:
        # Validate file size
        file.file.seek(0, 2)  # Seek to end of file
        file_size = file.file.tell()  # Get current position (file size)
        file.file.seek(0)  # Seek back to start

        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")

        # Create unique filename
        file_ext = Path(file.filename).suffix
        unique_filename = f"{Path(file.filename).stem}_{os.urandom(4).hex()}{file_ext}"
        file_path = settings.get_upload_dir() / unique_filename

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract text content (placeholder - implement actual text extraction)
        file_text_content = "Placeholder text content"

        # Create document record
        document = await DocumentModel(
            file_name=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            file_text_content=file_text_content,
        ).insert()

        return DocumentResponse(
            id=str(document.id),
            file_name=document.file_name,
            file_size=document.file_size,
            uploaded_at=document.uploaded_at,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[DocumentResponse])
async def list_documents():
    try:
        documents = await DocumentModel.find_all().to_list()
        return [
            DocumentResponse(
                id=str(doc.id),
                file_name=doc.file_name,
                file_size=doc.file_size,
                uploaded_at=doc.uploaded_at,
            )
            for doc in documents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/content")
async def get_document_content(document_id: str):
    try:
        document = await DocumentModel.get(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        file_path = Path(document.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document file not found")

        # Determine content type based on file extension
        content_type_map = {
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".txt": "text/plain",
            ".html": "text/html",
        }

        file_ext = Path(document.file_name).suffix.lower()
        media_type = content_type_map.get(file_ext, "application/octet-stream")

        return FileResponse(
            path=file_path,
            filename=document.file_name,
            media_type=media_type,
            content_disposition_type="inline",  # This makes the browser display the file instead of downloading
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[DocumentResponse])
async def search_documents(query: str = Query(..., min_length=1)):
    try:
        # Create a case-insensitive regex pattern for MongoDB
        documents = await DocumentModel.find(
            {
                "file_name": {"$regex": query, "$options": "i"}
            }  # 'i' option makes it case-insensitive
        ).to_list()

        return [
            DocumentResponse(
                id=str(doc.id),
                file_name=doc.file_name,
                file_size=doc.file_size,
                uploaded_at=doc.uploaded_at,
            )
            for doc in documents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{document_id}/ask", response_model=QuestionResponse)
async def ask_question(document_id: str, request: QuestionRequest):
    try:
        # Get the document
        document = await DocumentModel.get(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get the file path
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
