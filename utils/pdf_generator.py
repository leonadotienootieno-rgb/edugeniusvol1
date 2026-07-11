"""
PDF Generator for EduGenius (Optimized for fpdf2)
"""
import streamlit as st
import re
from fpdf import FPDF

def create_worksheet_pdf(worksheet_text, subject, topic, curriculum):
    # Initialize FPDF with A4 size
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Title Section
    pdf.set_font("Helvetica", "B", 16)
    # Using 190mm width for an A4 page (210mm total - 20mm margins)
    pdf.cell(190, 10, f"{curriculum} - {subject}", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(190, 8, f"Topic: {topic}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # Content Section
    pdf.set_font("Helvetica", "", 11)
    
    # 1. Clean the text: remove non-printable control characters
    # This prevents the "Not enough space" / "Unsupported character" crashes
    clean_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', worksheet_text)
    
    # 2. Split into paragraphs to maintain structure
    paragraphs = clean_text.split('\n')
    
    for para in paragraphs:
        if para.strip() == "":
            pdf.ln(4)
            continue
            
        # 3. Use multi_cell with 190mm width
        # 'split_only=False' forces wrapping based on page width
        pdf.multi_cell(190, 6, para.strip(), align='L')
            
    return pdf.output()

def generate_download_button(worksheet_text, subject, topic, curriculum):
    try:
        pdf_bytes = create_worksheet_pdf(worksheet_text, subject, topic, curriculum)
        
        # Clean filename to be filesystem safe
        safe_filename = f"{curriculum}_{subject}_{topic}".replace(" ", "_")[:50] + ".pdf"
        
        st.download_button(
            label="📥 Download as PDF",
            data=pdf_bytes,
            file_name=safe_filename,
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        # Show a helpful error to users instead of a hard crash
        st.warning("PDF generation is temporarily limited for this specific content. Please use the 'Copy Text' button instead.")
        # Optional: Print to logs for your debugging
        print(f"PDF Generation Error: {e}")
