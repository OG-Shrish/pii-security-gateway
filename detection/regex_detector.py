import re
from typing import List, Dict, Any

REGEX_PATTERNS = {
    "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    # Simple North American & International phone regex
    "PHONE": r'(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?',
    "CREDIT_CARD": r'\b(?:\d[ -]*?){13,16}\b',
    "IP_ADDRESS": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
}

def detect_regex(text: str) -> List[Dict[str, Any]]:
    findings = []
    
    for pii_type, pattern in REGEX_PATTERNS.items():
        for match in re.finditer(pattern, text):
            match_text = match.group(0)
            
            # Additional validation for credit card (Luhn check could go here)
            if pii_type == "CREDIT_CARD":
                digits = re.sub(r'\D', '', match_text)
                if len(digits) < 13 or len(digits) > 16:
                    continue
                    
            if pii_type == "PHONE":
                 # very basic phone filtering
                 digits = re.sub(r'\D', '', match_text)
                 if len(digits) < 10:
                     continue

            findings.append({
                "text": match_text,
                "start": match.start(),
                "end": match.end(),
                "pii_type": pii_type,
                "confidence": 0.95,
                "detection_method": "REGEX"
            })
            
    return findings
