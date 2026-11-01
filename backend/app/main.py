
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Evidence-First Policy Desk",
    description=(
        "An evidence-grounded multi-document "
        "AI question answering platform"
    ),
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Evidence-First Policy Desk API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
