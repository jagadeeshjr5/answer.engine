import aiohttp
import asyncio
import pdfplumber
from io import BytesIO

async def fetch_pdf_content(pdf_url):
    """Fetch PDF content asynchronously using aiohttp without creating a session."""
    async with aiohttp.ClientSession() as session:
        async with session.get(pdf_url, ssl=False) as response:
            if response.status == 200:
                return await response.read()  # Return the byte content of the PDF
            else:
                raise Exception(f"Failed to fetch PDF, status code: {response.status}")

async def extract_text_from_pdf(pdf_content):
    """Extract text from the PDF using pdfplumber, skipping unnecessary elements."""
    pdf_file = BytesIO(pdf_content)
    pdf_text = ""

    # Use pdfplumber to extract text
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                pdf_text += page_text

    # Remove any unnecessary whitespace or newlines
    pdf_text = " ".join(pdf_text.split())
    return pdf_text

async def process_pdf_url(pdf_url):
    """Fetch and extract text from a PDF URL."""
    pdf_content = await fetch_pdf_content(pdf_url)
    pdf_text = await extract_text_from_pdf(pdf_content)
    return pdf_text