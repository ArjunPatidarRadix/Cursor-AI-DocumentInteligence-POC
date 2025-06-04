import asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from ..database.models import DocumentModel
from ..config.settings import get_settings

settings = get_settings()

async def fix_document_path():
    # Initialize database connection
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[DocumentModel]
    )

    # Find the document
    document = await DocumentModel.find_one({"file_name": "B_08_03_W9123725Q0029_0001.pdf"})
    if document:
        # Update the file path
        document.file_path = f"{settings.UPLOAD_DIR}/20250522_112706_B_08_03_W9123725Q0029_0001.pdf"
        await document.save()
        print(f"Updated document path for {document.file_name}")
    else:
        print("Document not found")

if __name__ == "__main__":
    asyncio.run(fix_document_path()) 