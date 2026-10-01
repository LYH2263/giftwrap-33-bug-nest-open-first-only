from fastapi import APIRouter
from app.repositories import papers as repo
router = APIRouter()
@router.get("/papers")
def list_papers(): return {"items": repo.list_papers()}
