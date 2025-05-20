from fastapi import HTTPException, UploadFile, BackgroundTasks
from ..database.models import DocumentModel, DocumentResponse
from ..config.settings import get_settings
from .qa_service import qa_service
from .rag_service import rag_service
from .background_task_manager import background_task_manager
from pathlib import Path
import shutil
import os
from typing import List
import asyncio

settings = get_settings()

class DocumentService:
    @staticmethod
    async def _index_document_task(document_id: str) -> None:
        """The actual indexing task."""
        document = await DocumentModel.get(document_id)
        if not document:
            return
        await rag_service.index_document(document)

    @staticmethod
    async def _on_index_complete(task_id: str, _) -> None:
        """Callback when indexing completes successfully."""
        document = await DocumentModel.get(task_id)
        if document:
            document.indexing_status = "completed"
            document.indexing_error = None
            await document.save()

    @staticmethod
    async def _on_index_error(task_id: str, error: Exception) -> None:
        """Callback when indexing fails."""
        document = await DocumentModel.get(task_id)
        if document:
            document.indexing_status = "failed"
            document.indexing_error = str(error)
            await document.save()

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

            # Extract text content
            file_text_content = qa_service.extract_text_from_document(file_path)

            # Create document record with pending status
            document = await DocumentModel(
                file_name=file.filename,
                file_path=str(file_path),
                file_size=file_size,
                file_text_content=file_text_content,
                indexing_status="pending"
            ).insert()

            # Start background indexing task without awaiting it
            asyncio.create_task(
                background_task_manager.create_task(
                    task_id=str(document.id),
                    coro=DocumentService._index_document_task(str(document.id)),
                    on_complete=DocumentService._on_index_complete,
                    on_error=DocumentService._on_index_error
                )
            )

            return DocumentResponse(
                id=str(document.id),
                file_name=document.file_name,
                file_size=document.file_size,
                uploaded_at=document.uploaded_at,
                indexing_status=document.indexing_status,
                indexing_error=document.indexing_error
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
                    indexing_status=doc.indexing_status,
                    indexing_error=doc.indexing_error
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
                    indexing_status=doc.indexing_status,
                    indexing_error=doc.indexing_error
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