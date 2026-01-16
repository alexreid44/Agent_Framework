"""File generation utilities for PDF and Word documents."""

from pathlib import Path
from datetime import datetime
import re
from html.parser import HTMLParser


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
    """Save research report as PDF using xhtml2pdf.

    Args:
        output_dir: Directory to save the file
        base_filename: Base filename without extension
        company_name: Company name for title
        company_url: Company URL for metadata
        content: Research content in HTML format

    Returns:
        Path to the saved PDF file
    """
    from xhtml2pdf import pisa

    pdf_file = output_dir / f"{base_filename}.pdf"

    # Create full HTML document with styling
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: letter;
                margin: 0.75in;
            }}
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                text-align: center;
                font-size: 24pt;
            }}
            h2 {{
                color: #34495e;
                border-bottom: 2px solid #95a5a6;
                padding-bottom: 8px;
                margin-top: 20pt;
                font-size: 18pt;
            }}
            h3 {{
                color: #7f8c8d;
                margin-top: 15pt;
                font-size: 14pt;
            }}
            h4 {{
                color: #95a5a6;
                margin-top: 12pt;
                font-size: 12pt;
            }}
            p {{
                margin: 10px 0;
                text-align: justify;
            }}
            ul, ol {{
                margin: 10px 0;
                padding-left: 30px;
            }}
            li {{
                margin: 5px 0;
            }}
            strong {{
                color: #2c3e50;
            }}
            .metadata {{
                color: #7f8c8d;
                font-size: 10pt;
                margin-bottom: 30px;
                text-align: center;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
                page-break-inside: avoid;
            }}
            th {{
                background-color: #34495e;
                color: white;
                padding: 8px;
                text-align: left;
                font-weight: bold;
            }}
            td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            a {{
                color: #3498db;
                word-wrap: break-word;
            }}
        </style>
    </head>
    <body>
        <h1>Strategic Pursuit Plan: {company_name}</h1>
        <div class="metadata">
            <p><strong>Company URL:</strong> {company_url}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        <hr>
        {content}
    </body>
    </html>
    """

    # Generate PDF from HTML
    with open(pdf_file, "wb") as f:
        pisa_status = pisa.CreatePDF(full_html, dest=f)

    if pisa_status.err:
        raise Exception(f"PDF generation failed with error code: {pisa_status.err}")

    return pdf_file


class HTMLToDocxParser(HTMLParser):
    """Parse HTML and convert to Word document structure."""

    def __init__(self, doc):
        super().__init__()
        self.doc = doc
        self.current_paragraph = None
        self.in_list = False
        self.in_bold = False
        self.in_italic = False
        self.in_heading = False
        self.heading_level = 0
        self.heading_text = ""

    def handle_starttag(self, tag, attrs):
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.in_heading = True
            self.heading_level = int(tag[1])
            self.heading_text = ""
        elif tag == 'p':
            self.current_paragraph = self.doc.add_paragraph()
        elif tag in ['ul', 'ol']:
            self.in_list = True
        elif tag == 'li':
            if not self.current_paragraph:
                self.current_paragraph = self.doc.add_paragraph(style='List Bullet')
        elif tag == 'strong' or tag == 'b':
            self.in_bold = True
        elif tag == 'em' or tag == 'i':
            self.in_italic = True
        elif tag == 'br':
            if self.current_paragraph:
                self.current_paragraph.add_run('\n')

    def handle_endtag(self, tag):
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            if self.heading_text.strip():
                self.doc.add_heading(self.heading_text.strip(), level=self.heading_level)
            self.in_heading = False
            self.heading_text = ""
        elif tag == 'p':
            self.current_paragraph = None
        elif tag in ['ul', 'ol']:
            self.in_list = False
        elif tag == 'li':
            self.current_paragraph = None
        elif tag == 'strong' or tag == 'b':
            self.in_bold = False
        elif tag == 'em' or tag == 'i':
            self.in_italic = False

    def handle_data(self, data):
        if not data.strip():
            return

        if self.in_heading:
            self.heading_text += data
        elif self.current_paragraph:
            run = self.current_paragraph.add_run(data)
            if self.in_bold:
                run.bold = True
            if self.in_italic:
                run.italic = True


def save_business_model_canvas_docx(output_dir: Path, base_filename: str,
                                   company_name: str, company_url: str,
                                   content: str) -> Path:
    """Save Business Model Canvas as Word document from HTML content.

    Args:
        output_dir: Directory to save the file
        base_filename: Base filename without extension
        company_name: Company name for title
        company_url: Company URL for metadata
        content: Business Model Canvas HTML content

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

    # Parse HTML content and add to document
    parser = HTMLToDocxParser(doc)
    parser.feed(content)

    doc.save(str(docx_file))
    return docx_file
