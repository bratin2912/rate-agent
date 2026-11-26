
from fastapi import FastAPI
from app.api.health import router as health_router

app = FastAPI(
    title="Insurance Rater API",
    description="AI-powered motor insurance commission rating application",
    version="1.0.0"
)

app.include_router(health_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "Welcome to Insurance Rater API",
        "status": "running"
    }
