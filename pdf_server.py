"""
PDF Server Endpoint for Streamlit
Serves PDF files with page navigation support
"""
from pathlib import Path
from config import DATA_DIR, DOCUMENTS_DIR
import streamlit as st

@st.cache_data
def get_pdf_bytes(pdf_path: Path) -> bytes:
    """Get PDF file bytes for serving"""
    try:
        with open(pdf_path, 'rb') as f:
            return f.read()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return b""

def serve_pdf(pdf_path: Path, page_number: int = 1):
    """
    Serve PDF file in Streamlit with page navigation
    Note: Streamlit's st.pdf() doesn't support page anchors directly
    This provides the PDF viewer, users can navigate to the page manually
    """
    if not pdf_path.exists():
        st.error(f"PDF file not found: {pdf_path}")
        return
    
    try:
        # Display PDF with Streamlit's PDF viewer
        pdf_bytes = get_pdf_bytes(pdf_path)
        st.pdf(pdf_bytes)
        
        # Show page number hint
        st.info(f"📑 Navigate to page {page_number} in the PDF viewer above")
    except Exception as e:
        st.error(f"Error displaying PDF: {e}")

