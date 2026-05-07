from dataclasses import dataclass

@dataclass
class FeedbackSchema():
    user: str = ""
    comment: str = ""
    rating: int = 0
