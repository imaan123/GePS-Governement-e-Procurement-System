from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class BidderField:

    field_name: str
    field_type: str

    value: Any
    
    source_document: Optional[str] = None
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    original_text: Optional[str] = None

    confidence: float = 1.0