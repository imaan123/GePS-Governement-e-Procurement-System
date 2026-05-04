from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def placeholder():
    return {"msg": "feedback_routes placeholder"}
