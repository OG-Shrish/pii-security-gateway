import fitz  # PyMuPDF
from typing import List
from models.schemas import DocumentBlock

def extract_pdf(file_path: str, document_id: str, original_file_name: str) -> List[DocumentBlock]:
    blocks = []
    try:
        doc = fitz.open(file_path)
        order = 0
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            if not text.strip():
                # Handling for scanned pages (OCR placeholder)
                blocks.append(DocumentBlock(
                    document_id=document_id,
                    file_name=original_file_name,
                    file_type="pdf",
                    location=f"page_{page_num+1}",
                    block_type="SCANNED_PAGE_REQUIRES_OCR",
                    text="[SCANNED_PAGE_REQUIRES_OCR]",
                    order=order
                ))
                order += 1
                continue
            
            # Basic block extraction
            # get_text("blocks") returns a list of tuples: (x0, y0, x1, y1, text, block_no, block_type)
            page_blocks = page.get_text("blocks")
            for b in page_blocks:
                block_text = b[4].strip()
                block_type_int = b[6] # 0 for text, 1 for image
                if block_text and block_type_int == 0:
                    blocks.append(DocumentBlock(
                        document_id=document_id,
                        file_name=original_file_name,
                        file_type="pdf",
                        location=f"page_{page_num+1}",
                        block_type="text",
                        text=block_text,
                        order=order
                    ))
                    order += 1
    except Exception as e:
        raise Exception(f"Failed to read PDF file: {str(e)}")
    
    return blocks
