import asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from ..database.models import DocumentModel
from ..config.settings import get_settings
from ..services.document_analysis_service import document_analysis_service
import logging

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

document_id = "682f0d50587041a7d5b1aa7b"  # Change this if needed

async def run_full_analysis():
    # Initialize database connection
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[DocumentModel]
    )

    # Find the document
    document = await DocumentModel.get(document_id)
    if document:
        try:
            logger.info(f"Running full analysis for {document.file_name}")
            result = await document_analysis_service.analyze_document(document)
            logger.info(f"Analysis result: {result}")
        except Exception as e:
            logger.error(f"Error during full analysis: {str(e)}", exc_info=True)
    else:
        logger.error("Document not found")

if __name__ == "__main__":
    asyncio.run(run_full_analysis()) 