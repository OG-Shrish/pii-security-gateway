import os
from typing import List
from models.schemas import DocumentBlock

def extract_txt(file_path: str, document_id: str, original_file_name: str) -> List[DocumentBlock]:
    blocks = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Split by paragraphs
            paragraphs = content.split('\n\n')
            order = 0
            for i, para in enumerate(paragraphs):
                para = para.strip()
                if para:
                    blocks.append(DocumentBlock(
                        document_id=document_id,
                        file_name=original_file_name,
                        file_type="txt",
                        location=f"paragraph_{i+1}",
                        block_type="text",
                        text=para,
                        order=order
                    ))
                    order += 1
    except Exception as e:
        raise Exception(f"Failed to read TXT file: {str(e)}")
    
    return blocks
