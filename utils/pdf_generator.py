"""
PDF Generator for EduGenius (Optimized for fpdf2)
"""
import streamlit as st
import re
from datetime import datetime
from fpdf import FPDF

def sanitize_text(text):
    # Standard character replacements to avoid encoding issues
    replacements = {'–': '-', '—': '-', '•': '-', '“': '"', '”': '"', '‘': "'", '’': "'", '…': '...'}
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Remove non-printable characters
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

def create_worksheet_pdf(worksheet_text, subject, topic, curriculum):
    pdf = FPDF()
    pdf.add_page()
    
    # Title Section
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"{curriculum} - {subject}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Topic: {topic}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # Content Section
    pdf.set_font("Helvetica", "", 11)
    lines = worksheet_text.split('\n')
    
    for line in lines:
        line = sanitize_text(line.strip())
        if not line:
            pdf.ln(4)
        else:
            # fpdf2 handles UTF-8 automatically if you don't force latin-1
            # Using multi_cell with new_x/new_y for proper flow
            pdf.multi_cell(0, 6, line, align='L')
            
    return pdf.output() # Returns bytes directly in fpdf2

def generate_download_button(worksheet_text, subject, topic, curriculum):
    try:
        pdf_bytes = create_worksheet_pdf(worksheet_text, subject, topic, curriculum)
        st.download_button(
            label="📥 Download as PDF",
            data=pdf_bytes,
            file_name=f"{subject}_{topic}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"PDF Error: {e}")
