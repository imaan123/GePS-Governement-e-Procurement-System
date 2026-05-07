from dataclasses import dataclass
from typing import Optional, Dict, List


@dataclass
class Rule:
    rule_id: str
    rule_type: str
    category: str
    priority: int
    dependencies: Optional[List[str]]
    rule_definition: Dict
    confidence: float
    original_text: Optional[str] = None
    
