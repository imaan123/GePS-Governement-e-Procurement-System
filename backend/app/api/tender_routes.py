from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def placeholder():
    return {"msg": "tender_routes placeholder"}
