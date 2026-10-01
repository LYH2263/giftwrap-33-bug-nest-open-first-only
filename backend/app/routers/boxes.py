from fastapi import APIRouter, HTTPException
from app.repositories import boxes as repo
router = APIRouter()
@router.get("/boxes")
def list_boxes(): return {"items": repo.list_boxes()}
@router.get("/boxes/{bid}")
def get_box(bid: int):
    r = repo.get_box(bid)
    if not r: raise HTTPException(404)
    return r
