
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.policies import router as policies_router
from app.database.init_db import initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Insurance Rater Agent",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(policies_router)
