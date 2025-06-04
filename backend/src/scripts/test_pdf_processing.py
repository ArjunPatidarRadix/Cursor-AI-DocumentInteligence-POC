import asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from ..database.models import DocumentModel
from ..config.settings import get_settings
from ..services.qa_service import qa_service
import logging

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_pdf_processing():
    # Initialize database connection
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[DocumentModel]
    )

    # Find the document
    document = await DocumentModel.find_one({"file_name": "B_08_03_W9123725Q0029_0001.pdf"})
    if document:
        try:
            logger.info(f"Testing PDF processing for {document.file_name}")
            logger.info(f"File path: {document.file_path}")
            
            # Try text extraction
            text = qa_service.extract_text_from_document(document.file_path)
            logger.info(f"Text extraction successful. First 100 chars: {text[:100]}")
            
            
            # Update document
            document.file_text_content = text
            document.indexing_status = "completed"
            await document.save()
            logger.info("Document updated successfully")
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            document.indexing_status = "failed"
            document.indexing_error = str(e)
            await document.save()
    else:
        logger.error("Document not found")

if __name__ == "__main__":
    asyncio.run(test_pdf_processing()) 