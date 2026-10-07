import uuid
from typing import List
from models.schemas import PIIFinding, DocumentBlock
from detection.regex_detector import detect_regex
from detection.ner_detector import detect_ner
from detection.context_rules import detect_context

def get_severity(pii_type: str) -> str:
    if pii_type in ["GOVERNMENT_ID", "CREDIT_CARD"]:
        return "CRITICAL"
    elif pii_type in ["EMPLOYEE_ID", "EMAIL", "PHONE", "PERSON"]:
        return "HIGH"
    elif pii_type in ["ADDRESS", "DATE_OF_BIRTH"]:
        return "MEDIUM"
    return "LOW"

def overlap(start1: int, end1: int, start2: int, end2: int) -> bool:
    return max(start1, start2) < min(end1, end2)

def merge_findings(findings: List[dict]) -> List[dict]:
    if not findings:
        return []
        
    # Sort by start position, then by length (longest first)
    findings.sort(key=lambda x: (x["start"], -(x["end"] - x["start"])))
    
    merged = []
    current = findings[0]
    
    for next_find in findings[1:]:
        if overlap(current["start"], current["end"], next_find["start"], next_find["end"]):
            # Merge logic: Pick highest confidence
            if next_find["confidence"] > current["confidence"]:
                current_methods = current["detection_method"].split(" + ") if isinstance(current["detection_method"], str) else [current["detection_method"]]
                next_methods = next_find["detection_method"].split(" + ") if isinstance(next_find["detection_method"], str) else [next_find["detection_method"]]
                methods = list(set(current_methods + next_methods))
                
                current = next_find
                current["detection_method"] = " + ".join(methods)
            else:
                current_methods = current["detection_method"].split(" + ") if isinstance(current["detection_method"], str) else [current["detection_method"]]
                next_methods = next_find["detection_method"].split(" + ") if isinstance(next_find["detection_method"], str) else [next_find["detection_method"]]
                methods = list(set(current_methods + next_methods))
                
                current["detection_method"] = " + ".join(methods)
        else:
            merged.append(current)
            current = next_find
            
    merged.append(current)
    return merged

def detect_pii_in_block(block: DocumentBlock) -> List[PIIFinding]:
    text = block.text
    if not text or text == "[SCANNED_PAGE_REQUIRES_OCR]":
        return []
        
    raw_findings = []
    raw_findings.extend(detect_regex(text))
    raw_findings.extend(detect_ner(text))
    raw_findings.extend(detect_context(text))
    
    # Filter out weak generic dates that aren't boosted by context
    filtered_findings = []
    for f in raw_findings:
        if f["pii_type"] == "DATE_OF_BIRTH" and f["confidence"] < 0.70:
            continue
        filtered_findings.append(f)
        
    merged_raw = merge_findings(filtered_findings)
    
    final_findings = []
    for f in merged_raw:
        final_findings.append(PIIFinding(
            finding_id=str(uuid.uuid4()),
            document_id=block.document_id,
            file_name=block.file_name,
            location=block.location,
            start=f["start"],
            end=f["end"],
            text=f["text"],
            pii_type=f["pii_type"],
            confidence=f["confidence"],
            detection_method=[m.strip() for m in f["detection_method"].split("+")],
            severity=get_severity(f["pii_type"])
        ))
        
    return final_findings
