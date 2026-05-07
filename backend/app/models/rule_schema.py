from dataclasses import dataclass
from typing import Optional, Dict, List, Any


@dataclass
class Rule:
    rule_id: str
    rule_type: str
    category: str
    priority: int
    dependencies: Optional[Dict[str, Any]]
    rule_definition: Dict
    confidence: float
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    original_text: Optional[str] = None
    
