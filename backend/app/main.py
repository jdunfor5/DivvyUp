from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.dependencies.database import check_db_connection, init_db

# Import all models so SQLModel sees them before create_all runs
import app.models.user       
import app.models.group      
import app.models.expense


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once on startup
    await check_db_connection()
    await init_db()
    yield
    # Runs on shutdown (add cleanup here if needed)


app = FastAPI(title="DivvyUp API", lifespan=lifespan)


@app.get("/")
def root():
    return {"message": "DivvyUp API is running!"}

@app.get("/health")
async def health():
    return {"status": "ok"}