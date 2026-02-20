import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import groups, expenses, users

# Initialize FastAPI app
app = FastAPI(
    title="DivvyUp API",
    description="API for managing shared expenses among friends",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
def root():
    return {"message": "DivvyUp API is running!"}

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Include routers from api folder
app.include_router(groups.router, prefix="/api/groups", tags=["Groups"])
app.include_router(expenses.router, prefix="/api/expenses", tags=["Expenses"])
app.include_router(expenses.router, prefix="/api/users", tags=["Users"])