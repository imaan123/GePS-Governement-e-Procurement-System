from dataclasses import dataclass
from typing import Optional

@dataclass
class EvaluationResult:
    bidder_id: str
    rule_id: str
    extracted_value: Optional[float]
    result: str
    confidence: float
    evidence_doc: Optional[str]
    evidence_page: Optional[int]
    evaluation_logic: str