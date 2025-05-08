import motor.motor_asyncio
from beanie import init_beanie
from ..config.settings import get_settings
from .models import DocumentModel

settings = get_settings()


async def init_db():
    # Create Motor client
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)

    # Initialize beanie with the Product document class
    await init_beanie(
        database=client[settings.DATABASE_NAME], document_models=[DocumentModel]
    )
