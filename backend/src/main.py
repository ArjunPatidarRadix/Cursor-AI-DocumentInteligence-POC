from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .database.connection import init_db
from .routers import documents
from .config.settings import get_settings

settings = get_settings()

# Define base directory
BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="Document Intelligence API",
    description="API for document processing and information extraction",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Include routers
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])


@app.on_event("startup")
async def startup_event():
    await init_db()


@app.get("/")
async def root():
    return {"message": "Welcome to Document Intelligence API", "status": "active"}
