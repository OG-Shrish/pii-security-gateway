from typing import List
from models.schemas import DocumentBlock, ValidationResult
from detection.pii_engine import detect_pii_in_block

def validate_sanitized_blocks(document_id: str, blocks: List[DocumentBlock]) -> ValidationResult:
    remaining_findings = []
    
    for block in blocks:
        # Re-run detection on the sanitized block
        findings = detect_pii_in_block(block)
        remaining_findings.extend(findings)
        
    # Check for high/critical severity or high confidence findings
    high_risk_remaining = [
        f for f in remaining_findings 
        if f.severity in ["CRITICAL", "HIGH"] or f.confidence >= 0.85
    ]
    
    is_safe = len(high_risk_remaining) == 0
    
    if is_safe:
        message = "No high-confidence PII remains. Document is safe."
    else:
        message = f"Residual PII detected ({len(high_risk_remaining)} high-risk findings). Document is blocked."
        
    return ValidationResult(
        document_id=document_id,
        is_safe=is_safe,
        remaining_findings=remaining_findings,
        message=message
    )
