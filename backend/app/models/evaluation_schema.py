from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class EvaluationResult:
    bidder_id: str
    rule_id: str
    field: str
    bidder_value: Any
    expected_value: Any
    result: str
    rule_type: str
    confidence: float
    source_document: Optional[str] = None
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    bidder_original_text: Optional[str] = None
    bidder_confidence: Optional[float] = None
    rule_original_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class EvaluationSummary:
    bidder_id: str
    verdict: str
    mandatory_count: int
    total_rules: int
    passed_count: int
    failed_count: int
    needs_review_count: int
