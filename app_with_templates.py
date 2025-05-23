from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import uuid
import json
from browser_pdf_generator import BrowserPDFGenerator, load_json_data, generate_pdf_with_playwright, generate_pdf_with_playwright_async

app = FastAPI(title="Proposal PDF Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

generator = BrowserPDFGenerator()

@app.post("/generate-pdf/")
def generate_pdf_from_json(
    data_file: UploadFile = File(...)
):
    """
    Accept a JSON file (in the format of sample_data.json), generate a PDF (like invest4edu_report_output.pdf)
    using the invest4edu_report.html template, and return the PDF as a download.
    """
    # Save the uploaded JSON
    json_filename = f"input_{uuid.uuid4().hex}.json"
    json_path = os.path.join(UPLOAD_DIR, json_filename)
    with open(json_path, "wb") as buffer:
        shutil.copyfileobj(data_file.file, buffer)

    # Load data and check
    data = load_json_data(json_path)
    if not data:
        return JSONResponse({"error": "Invalid JSON data."}, status_code=400)

    # Get template from data or use default
    html_filename = f"report_{uuid.uuid4().hex}.html"
    html_path = os.path.join(OUTPUT_DIR, html_filename)
    
    # Use the template specified in the data or default to invest4edu
    template_name = "invest4edu_report.html"  # Default template
    pdf_output_name = "invest4edu_report_output.pdf"
    
    # Check for template in the data
    if isinstance(data, dict) and "template" in data:
        if data["template"].lower() == "investvalue":
            template_name = "investvalue_report.html"
            pdf_output_name = "investvalue_report_output.pdf"
    
    generator.generate_html(template_name, data, html_path)

    # Generate PDF from HTML
    pdf_filename = f"output_{uuid.uuid4().hex}.pdf"
    pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)
    
    try:
        pdf_success = generate_pdf_with_playwright(html_path, pdf_path)
        if not pdf_success or not os.path.exists(pdf_path):
            return JSONResponse({"error": "PDF generation failed."}, status_code=500)
    except Exception as e:
        print(f"Error during PDF generation: {str(e)}")
        return JSONResponse({"error": f"PDF generation error: {str(e)}"}, status_code=500)

    return FileResponse(pdf_path, media_type="application/pdf", filename=pdf_output_name)

from fastapi import Body

@app.post("/generate-pdf-json/")
async def generate_pdf_from_json_body(
    data: dict = Body(..., example={
        "clientname": "Akhilesh Gupta",
        "report_title": "Investment Report",
        "template": "invest4edu",  # Can be "invest4edu" or "investvalue"
        "logo_url": "",
        "investment_products": {"target": "1.00Cr"}
        # ... (rest of your sample_data.json structure)
    })
):
    """
    Accept JSON data in the request body, generate a PDF (like invest4edu_report_output.pdf)
    using the invest4edu_report.html template, and return the PDF as a download.
    """
    # Save JSON to a temp file for compatibility
    json_filename = f"input_{uuid.uuid4().hex}.json"
    json_path = os.path.join(UPLOAD_DIR, json_filename)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Get template from data or use default
    html_filename = f"report_{uuid.uuid4().hex}.html"
    html_path = os.path.join(OUTPUT_DIR, html_filename)
    
    # Use the template specified in the data or default to invest4edu
    template_name = "invest4edu_report.html"  # Default template
    pdf_output_name = "invest4edu_report_output.pdf"
    
    # Check for template in the data
    if "template" in data:
        if data["template"].lower() == "investvalue":
            template_name = "investvalue_report.html"
            pdf_output_name = "investvalue_report_output.pdf"
    
    generator.generate_html(template_name, data, html_path)

    # Generate PDF from HTML
    pdf_filename = f"output_{uuid.uuid4().hex}.pdf"
    pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)
    
    try:
        pdf_success = await generate_pdf_with_playwright_async(html_path, pdf_path)
        if not pdf_success or not os.path.exists(pdf_path):
            return JSONResponse({"error": "PDF generation failed."}, status_code=500)
    except Exception as e:
        print(f"Error during PDF generation: {str(e)}")
        return JSONResponse({"error": f"PDF generation error: {str(e)}"}, status_code=500)

    return FileResponse(pdf_path, media_type="application/pdf", filename=pdf_output_name)

@app.get("/")
def root():
    return HTMLResponse("""
    <h2>Proposal PDF Generator API</h2>
    <ul>
        <li>POST a JSON file to <code>/generate-pdf/</code> to receive the generated PDF.</li>
        <li>POST raw JSON to <code>/generate-pdf-json/</code> to receive the generated PDF.</li>
    </ul>
    <ul>
        <li>Input: JSON data (like <code>sample_data.json</code>)</li>
        <li>Output: PDF file (like <code>invest4edu_report_output.pdf</code> or <code>investvalue_report_output.pdf</code>)</li>
    </ul>
    <p>To specify which template to use, include a <code>"template"</code> field in your JSON with either <code>"invest4edu"</code> or <code>"investvalue"</code> as the value.</p>
    """)
