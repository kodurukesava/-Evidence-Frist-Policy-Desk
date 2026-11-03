
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from . import models


# Create database tables during development
Base.metadata.create_all(bind=engine)


# Initialize FastAPI application
app = FastAPI(
    title="Evidence-First Policy Desk",
    description=(
        "An evidence-grounded multi-document "
        "AI question answering platform"
    ),
    version="1.0.0"
)


# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Home endpoint
@app.get("/")
def home():
    return {
        "message": "Evidence-First Policy Desk API",
        "status": "running"
    }


# Health check endpoint
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# Database status endpoint
@app.get("/database-status")
def database_status():
    return {
        "database": "connected",
        "tables": list(Base.metadata.tables.keys())
    }
