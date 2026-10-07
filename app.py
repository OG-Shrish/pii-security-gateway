import streamlit as st
import os
import uuid
import pandas as pd
from typing import List, Dict, Any

from models.schemas import DocumentAnalysisResult, DocumentBlock
from extractors.txt_extractor import extract_txt
from extractors.pdf_extractor import extract_pdf
from extractors.docx_extractor import extract_docx
from extractors.pptx_extractor import extract_pptx
from detection.pii_engine import detect_pii_in_block
from redaction.redactor import Redactor
from redaction.validator import validate_sanitized_blocks
from reporting.report_generator import generate_json_report, generate_csv_report

# Configuration
st.set_page_config(
    page_title="PII Security Gateway",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark theme styling
st.markdown("""
<style>
    .reportview-container {
        background: #0E1117;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        border-radius: 4px;
        border: none;
    }
    .status-badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85em;
    }
    .status-sanitized { background-color: #1b5e20; color: white; }
    .status-blocked { background-color: #b71c1c; color: white; }
    .status-error { background-color: #f57f17; color: white; }
    .security-notice {
        font-size: 0.8em;
        color: #9e9e9e;
        text-align: center;
        margin-top: -10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Helper for processing
def process_file(uploaded_file) -> DocumentAnalysisResult:
    file_name = uploaded_file.name
    file_ext = file_name.split('.')[-1].lower()
    document_id = str(uuid.uuid4())
    
    # Save temp file
    temp_path = os.path.join("uploads", file_name)
    os.makedirs("uploads", exist_ok=True)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    result = DocumentAnalysisResult(
        document_id=document_id,
        file_name=file_name,
        file_type=file_ext,
        status="PROCESSING",
        original_blocks=[],
        sanitized_blocks=[],
        findings=[]
    )
    
    try:
        # 1. Extract
        if file_ext == 'txt':
            blocks = extract_txt(temp_path, document_id, file_name)
        elif file_ext == 'pdf':
            blocks = extract_pdf(temp_path, document_id, file_name)
        elif file_ext == 'docx':
            blocks = extract_docx(temp_path, document_id, file_name)
        elif file_ext == 'pptx':
            blocks = extract_pptx(temp_path, document_id, file_name)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
            
        result.original_blocks = blocks
        
        # 2. Detect & 3. Redact
        redactor = Redactor()
        all_findings = []
        sanitized_blocks = []
        
        for block in blocks:
            # Detect
            findings = detect_pii_in_block(block)
            all_findings.extend(findings)
            
            # Redact
            sanitized_block, _ = redactor.redact_block(block, findings)
            sanitized_blocks.append(sanitized_block)
            
        result.findings = all_findings
        result.sanitized_blocks = sanitized_blocks
        
        # 4. Validate
        validation = validate_sanitized_blocks(document_id, sanitized_blocks)
        result.validation_result = validation
        
        # 5. Status
        if validation.is_safe:
            result.status = "SANITIZED"
        else:
            result.status = "BLOCKED"
            
    except Exception as e:
        result.status = "ERROR"
        result.error_message = str(e)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    return result


def main():
    st.title("🛡️ PII Security Gateway")
    st.markdown("### Detect • Classify • Redact • Validate")
    st.markdown("<p class='security-notice'>LOCAL PROCESSING • NO DATA SENT TO EXTERNAL AI SERVICES</p>", unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Upload Business Evidence Documents", 
        type=["pdf", "docx", "pptx", "txt"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        if st.button("Analyze Documents"):
            results = []
            
            # Create progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, uf in enumerate(uploaded_files):
                status_text.text(f"Processing {uf.name}...")
                res = process_file(uf)
                results.append(res)
                progress_bar.progress((i + 1) / len(uploaded_files))
                
            status_text.text("Analysis Complete.")
            st.session_state['analysis_results'] = results
            
    # Display Results if they exist
    if 'analysis_results' in st.session_state:
        results: List[DocumentAnalysisResult] = st.session_state['analysis_results']
        
        # --- Dashboard Summary ---
        st.header("Dashboard Summary")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        total_docs = len(results)
        total_pii = sum(len(r.findings) for r in results)
        high_risk = sum(1 for r in results for f in r.findings if f.severity in ["CRITICAL", "HIGH"])
        sanitized = sum(1 for r in results if r.status == "SANITIZED")
        blocked = sum(1 for r in results if r.status == "BLOCKED")
        
        col1.metric("Documents Analyzed", total_docs)
        col2.metric("PII Detected", total_pii)
        col3.metric("High Risk", high_risk)
        col4.metric("Sanitized", sanitized)
        col5.metric("Blocked", blocked)
        
        st.divider()
        
        # --- Select Document for details ---
        st.header("Document Detail View")
        doc_names = [r.file_name for r in results]
        selected_doc_name = st.selectbox("Select a document to view details:", doc_names)
        
        selected_result = next((r for r in results if r.file_name == selected_doc_name), None)
        
        if selected_result:
            # Status Badge
            badge_class = f"status-{selected_result.status.lower()}"
            st.markdown(f"<span class='status-badge {badge_class}'>STATUS: {selected_result.status}</span>", unsafe_allow_html=True)
            
            if selected_result.status == "ERROR":
                st.error(f"Processing Error: {selected_result.error_message}")
            else:
                # Document Tabs
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "Findings Table", 
                    "Source Traceability", 
                    "Original Text", 
                    "Sanitized Output", 
                    "Validation Result"
                ])
                
                with tab1:
                    if selected_result.findings:
                        findings_data = []
                        for f in selected_result.findings:
                            findings_data.append({
                                "Severity": f.severity,
                                "Type": f.pii_type,
                                "Confidence": f"{f.confidence*100:.1f}%",
                                "Method": " + ".join(f.detection_method),
                                "Location": f.location,
                                "Action": "REDACTED"
                            })
                        st.dataframe(pd.DataFrame(findings_data), use_container_width=True)
                    else:
                        st.info("No PII detected in this document.")
                        
                with tab2:
                    st.markdown("### Traceability Details")
                    if selected_result.findings:
                        for f in selected_result.findings:
                            with st.expander(f"{f.pii_type} at {f.location}"):
                                st.write(f"**Document:** {selected_result.file_name}")
                                st.write(f"**Finding:** {f.pii_type}")
                                st.write(f"**Location:** {f.location}")
                                st.write(f"**Confidence:** {f.confidence*100:.1f}%")
                                st.write(f"**Method:** {' + '.join(f.detection_method)}")
                    else:
                        st.info("No PII detected.")
                        
                with tab3:
                    st.markdown("*(Only shown locally for review)*")
                    original_text = "\n\n".join([b.text for b in selected_result.original_blocks])
                    st.text_area("Original Content", original_text, height=400, disabled=True)
                    
                with tab4:
                    sanitized_text = "\n\n".join([b.text for b in selected_result.sanitized_blocks])
                    st.text_area("Sanitized Content", sanitized_text, height=400, disabled=True)
                    
                    st.download_button(
                        "Download Sanitized Text",
                        sanitized_text,
                        file_name=f"sanitized_{selected_result.file_name}.txt"
                    )
                    
                with tab5:
                    val = selected_result.validation_result
                    if val:
                        if val.is_safe:
                            st.success(val.message)
                        else:
                            st.error(val.message)
                            st.write("Remaining PII findings:")
                            rem_data = [{"Type": f.pii_type, "Text": f.text, "Confidence": f.confidence} for f in val.remaining_findings]
                            st.dataframe(pd.DataFrame(rem_data))
                            
        st.divider()
        
        # --- Reporting ---
        st.header("Reports")
        json_report = generate_json_report(results)
        csv_report = generate_csv_report(results)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("Download JSON Report", json_report, "report.json", "application/json")
        with col2:
            st.download_button("Download CSV Report", csv_report, "report.csv", "text/csv")


if __name__ == "__main__":
    main()
