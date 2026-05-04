from pydantic import BaseModel

class RuleSchema(BaseModel):
    name: str = ""
    pattern: str = ""
