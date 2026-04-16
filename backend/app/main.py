from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.dependencies.database import check_db_connection, init_db
from app.dependencies.config import settings
from app.api.middleware.error_handler import ErrorHandlerMiddleware

# Import all models so SQLModel sees them before create_all runs
import app.models.user
import app.models.group
import app.models.expense

# Import all routers
from app.api.routers.loader import load_routers

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once on startup
    await check_db_connection()
    await init_db()
    yield
    # Runs on shutdown (add cleanup here if needed)

app = FastAPI(title="DivvyUp API", lifespan=lifespan)

app.add_middleware(ErrorHandlerMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

load_routers(app)

@app.get("/")
def root():
    return {"message": "DivvyUp API is running!"}

@app.get("/health")
async def health():
    return {"status": "ok"}