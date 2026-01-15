"""File generation utilities for PDF and Word documents."""

from pathlib import Path
from datetime import datetime


def generate_filename(company_name: str, suffix: str = "") -> tuple[str, str]:
    """Generate timestamped filename and sanitized company name.

    Args:
        company_name: The company name to sanitize
        suffix: Optional suffix to add (e.g., "_BusinessModelCanvas")

    Returns:
        Tuple of (base_filename, timestamp)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_company_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in company_name)
    safe_company_name = safe_company_name.replace(' ', '_')
    base_filename = f"{timestamp}_{safe_company_name}{suffix}"
    return base_filename, timestamp


def save_research_pdf(output_dir: Path, base_filename: str, company_name: str,
                     company_url: str, content: str) -> Path:
    """Save research report as PDF.

    Args:
        output_dir: Directory to save the file
        base_filename: Base filename without extension
        company_name: Company name for title
        company_url: Company URL for metadata
        content: Research content to save

    Returns:
        Path to the saved PDF file
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    pdf_file = output_dir / f"{base_filename}.pdf"
    doc = SimpleDocTemplate(str(pdf_file), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, spaceAfter=30)
    story.append(Paragraph(f"Strategic Pursuit Plan: {company_name}", title_style))
    story.append(Spacer(1, 0.2*inch))

    # Metadata
    story.append(Paragraph(f"<b>Company URL:</b> {company_url}", styles['Normal']))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    # Content - split by lines and create paragraphs
    for line in content.split('\n'):
        if line.strip():
            story.append(Paragraph(line.replace('<', '&lt;').replace('>', '&gt;'), styles['Normal']))
            story.append(Spacer(1, 0.1*inch))

    doc.build(story)
    return pdf_file


def save_business_model_canvas_docx(output_dir: Path, base_filename: str,
                                   company_name: str, company_url: str,
                                   content: str) -> Path:
    """Save Business Model Canvas as Word document.

    Args:
        output_dir: Directory to save the file
        base_filename: Base filename without extension
        company_name: Company name for title
        company_url: Company URL for metadata
        content: Business Model Canvas markdown content

    Returns:
        Path to the saved DOCX file
    """
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    docx_file = output_dir / f"{base_filename}.docx"
    doc = Document()

    # Title
    title = doc.add_heading(f"Business Model Canvas: {company_name}", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Metadata
    metadata = doc.add_paragraph()
    metadata.add_run(f"Company URL: ").bold = True
    metadata.add_run(company_url)

    timestamp_para = doc.add_paragraph()
    timestamp_para.add_run(f"Generated: ").bold = True
    timestamp_para.add_run(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    doc.add_paragraph()  # Empty line
    doc.add_paragraph("_" * 80)  # Separator
    doc.add_paragraph()

    # Content - parse markdown and add to document
    lines = content.split('\n')
    for line in lines:
        if line.strip():
            if line.startswith('# '):
                doc.add_heading(line.lstrip('# ').strip(), level=1)
            elif line.startswith('## '):
                doc.add_heading(line.lstrip('## ').strip(), level=2)
            elif line.startswith('### '):
                doc.add_heading(line.lstrip('### ').strip(), level=3)
            elif line.startswith('**') and line.endswith('**'):
                p = doc.add_paragraph()
                p.add_run(line.strip('*')).bold = True
            elif line.startswith('- ') or line.startswith('* '):
                doc.add_paragraph(line.lstrip('-* ').strip(), style='List Bullet')
            else:
                doc.add_paragraph(line)

    doc.save(str(docx_file))
    return docx_file
