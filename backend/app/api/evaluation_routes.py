from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def placeholder():
    return {"msg": "evaluation_routes placeholder"}
