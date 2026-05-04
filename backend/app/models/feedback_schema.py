from pydantic import BaseModel

class FeedbackSchema(BaseModel):
    user: str = ""
    comment: str = ""
    rating: int = 0
