from pydantic import BaseModel

class BidderSchema(BaseModel):
    name: str = ""
    documents: list = []
