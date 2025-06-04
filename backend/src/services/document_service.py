from fastapi import HTTPException, UploadFile, BackgroundTasks
from ..database.models import DocumentModel, DocumentResponse
from ..config.settings import get_settings
from .qa_service import qa_service
from .rag_service import rag_service
from .document_analysis_service import document_analysis_service
from .background_task_manager import background_task_manager
from pathlib import Path
import shutil
import os
from typing import List, Dict, Any
import asyncio
import logging
from datetime import datetime

settings = get_settings()
logger = logging.getLogger(__name__)

class DocumentService:
    # Allowed file types and their max sizes (in bytes)
    ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.html'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    @staticmethod
    async def validate_document(file: UploadFile) -> None:
        """Validate document before processing."""
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in DocumentService.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Supported types: {', '.join(DocumentService.ALLOWED_EXTENSIONS)}"
            )

        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset file pointer

        if file_size > DocumentService.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {DocumentService.MAX_FILE_SIZE / (1024 * 1024)}MB"
            )

    @staticmethod
    async def _update_processing_progress(document: DocumentModel, step: str, progress: float) -> None:
        """Update processing progress for a specific step."""
        document.processing_progress[step] = progress
        await document.save()

    @staticmethod
    async def _handle_processing_error(document: DocumentModel, step: str, error: Exception) -> None:
        """Handle processing errors with retry mechanism."""
        document.processing_retries[step] += 1
        retries = document.processing_retries[step]

        if retries >= document.max_retries:
            document.indexing_status = "failed"
            document.indexing_error = f"Failed to process {step} after {retries} attempts: {str(error)}"
            logger.error(f"Processing failed for document {document.file_name}: {str(error)}")
        else:
            logger.warning(f"Retrying {step} for document {document.file_name} (attempt {retries})")
            # Schedule retry
            await asyncio.sleep(2 ** retries)  # Exponential backoff
            await DocumentService._index_document_task(str(document.id))

        await document.save()

    @staticmethod
    async def _index_document_task(document_id: str) -> None:
        """The actual indexing task with enhanced error handling and progress tracking."""
        document = await DocumentModel.get(document_id)
        if not document:
            return

        try:
            document.indexing_status = "processing"
            await document.save()

            # Text extraction
            try:
                await DocumentService._update_processing_progress(document, "text_extraction", 0.2)
                document.file_text_content = qa_service.extract_text_from_document(document.file_path)
                await DocumentService._update_processing_progress(document, "text_extraction", 1.0)
            except Exception as e:
                await DocumentService._handle_processing_error(document, "text_extraction", e)
                return

            # Document analysis
            try:
                analysis_tasks = [
                    ("classification", 0.3),
                    ("entity_extraction", 0.4),
                    ("table_extraction", 0.5),
                    ("summarization", 0.6)
                ]

                for step, progress in analysis_tasks:
                    await DocumentService._update_processing_progress(document, step, progress)

                analysis_results = await document_analysis_service.analyze_document(document)
                document.file_extracted_details = analysis_results

                for step, _ in analysis_tasks:
                    await DocumentService._update_processing_progress(document, step, 1.0)

            except Exception as e:
                await DocumentService._handle_processing_error(document, "document_analysis", e)
                return

            # RAG indexing
            try:
                await DocumentService._update_processing_progress(document, "rag_indexing", 0.7)
                await rag_service.index_document(document)
                await DocumentService._update_processing_progress(document, "rag_indexing", 1.0)
            except Exception as e:
                await DocumentService._handle_processing_error(document, "rag_indexing", e)
                return

            # Mark as completed
            document.indexing_status = "completed"
            document.indexing_error = None
            await document.save()

            logger.info(f"Document processing completed successfully for {document.file_name}")

        except Exception as e:
            logger.error(f"Unexpected error during document processing: {str(e)}")
            document.indexing_status = "failed"
            document.indexing_error = f"Unexpected error: {str(e)}"
            await document.save()

    @staticmethod
    async def _on_index_complete(task_id: str, _) -> None:
        """Callback when indexing completes successfully."""
        document = await DocumentModel.get(task_id)
        if document:
            if document.indexing_status != "failed":
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
        """Upload and process a document."""
        try:
            # Validate document
            await DocumentService.validate_document(file)

            # Create upload directory if it doesn't exist
            upload_dir = Path(settings.UPLOAD_DIR)
            upload_dir.mkdir(parents=True, exist_ok=True)

            # Generate unique filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_name = f"{timestamp}_{file.filename}"
            file_path = upload_dir / file_name

            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Get file size
            file_size = os.path.getsize(file_path)

            # Create document record
            document = await DocumentModel(
                file_name=file.filename,
                file_path=str(file_path),
                file_size=file_size,
                file_text_content="",  # Will be populated during processing
                indexing_status="pending"
            ).insert()

            # Start background processing
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
            logger.error(f"Error uploading document: {str(e)}")
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

    @staticmethod
    async def get_document_analysis(document_id: str) -> dict:
        """Get document analysis results."""
        document = await DocumentModel.get(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if not document.file_extracted_details:
            raise HTTPException(
                status_code=400,
                detail="Document analysis not available. Please wait for indexing to complete."
            )
        
        return document.file_extracted_details

# Create a singleton instance
document_service = DocumentService() 