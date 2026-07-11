"""
PDF Generator for EduGenius (Optimized for fpdf2)
"""
import streamlit as st
import re
from fpdf import FPDF

def create_worksheet_pdf(worksheet_text, subject, topic, curriculum):
    # Initialize fpdf2
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Title Section
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, f"{curriculum} - {subject}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(190, 8, f"Topic: {topic}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # Content Section
    pdf.set_font("Helvetica", "", 11)
    
    # Clean the text: remove non-printable characters
    clean_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', worksheet_text)
    
    # Use multi_cell with a fixed width (190mm is standard for A4) 
    # to prevent the "horizontal space" error.
    pdf.multi_cell(190, 6, clean_text, align='L')
            
    return pdf.output()

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
        st.error(f"PDF generation failed. Please try a different topic.")
