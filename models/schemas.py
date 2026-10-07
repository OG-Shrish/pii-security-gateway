from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class DocumentBlock:
    document_id: str
    file_name: str
    file_type: str
    location: str
    block_type: str
    text: str
    order: int

@dataclass
class PIIFinding:
    finding_id: str
    document_id: str
    file_name: str
    location: str
    start: int
    end: int
    text: str
    pii_type: str
    confidence: float
    detection_method: List[str]
    severity: str

@dataclass
class RedactionResult:
    document_id: str
    original_text: str
    sanitized_text: str
    findings: List[PIIFinding]
    placeholder_map: Dict[str, str]

@dataclass
class ValidationResult:
    document_id: str
    is_safe: bool
    remaining_findings: List[PIIFinding]
    message: str

@dataclass
class DocumentAnalysisResult:
    document_id: str
    file_name: str
    file_type: str
    status: str
    original_blocks: List[DocumentBlock]
    sanitized_blocks: List[DocumentBlock]
    findings: List[PIIFinding]
    validation_result: Optional[ValidationResult] = None
    error_message: Optional[str] = None
