from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def placeholder():
    return {"msg": "bidder_routes placeholder"}
