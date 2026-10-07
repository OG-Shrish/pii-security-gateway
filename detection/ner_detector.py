import spacy
from typing import List, Dict, Any

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None

def detect_ner(text: str) -> List[Dict[str, Any]]:
    findings = []
    if not nlp:
        return findings
        
    doc = nlp(text)
    
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            findings.append({
                "text": ent.text,
                "start": ent.start_char,
                "end": ent.end_char,
                "pii_type": "PERSON",
                "confidence": 0.85,
                "detection_method": "NER"
            })
        elif ent.label_ in ["GPE", "LOC"]:
            findings.append({
                "text": ent.text,
                "start": ent.start_char,
                "end": ent.end_char,
                "pii_type": "ADDRESS", # mapped from GPE/LOC
                "confidence": 0.70, # Lower confidence for generic locations
                "detection_method": "NER"
            })
        elif ent.label_ == "DATE":
             findings.append({
                "text": ent.text,
                "start": ent.start_char,
                "end": ent.end_char,
                "pii_type": "DATE_OF_BIRTH", # context will boost this
                "confidence": 0.50, # Low initial confidence, needs context
                "detection_method": "NER"
            })
            
    return findings
