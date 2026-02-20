from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def groups_health():
    return {"status": "users endpoint healthy"}