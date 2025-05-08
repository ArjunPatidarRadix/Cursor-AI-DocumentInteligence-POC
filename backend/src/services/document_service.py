from fastapi import HTTPException, UploadFile
from ..database.models import DocumentModel, DocumentResponse
from ..config.settings import get_settings
from pathlib import Path
import shutil
import os
from typing import List

settings = get_settings()

class DocumentService:
    @staticmethod
    async def upload_document(file: UploadFile) -> DocumentResponse:
        try:
            # Validate file size
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)

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

    @staticmethod
    async def list_documents() -> List[DocumentResponse]:
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

    @staticmethod
    async def get_document(document_id: str) -> DocumentModel:
        document = await DocumentModel.get(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document

    @staticmethod
    async def search_documents(query: str) -> List[DocumentResponse]:
        try:
            documents = await DocumentModel.find(
                {"file_name": {"$regex": query, "$options": "i"}}
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

    @staticmethod
    def get_content_type(file_name: str) -> str:
        content_type_map = {
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".txt": "text/plain",
            ".html": "text/html",
        }
        file_ext = Path(file_name).suffix.lower()
        return content_type_map.get(file_ext, "application/octet-stream")

# Create a singleton instance
document_service = DocumentService() 