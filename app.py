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
async def generate_pdf_from_json(
    data_file: UploadFile = File(...),
    template: str = "invest4edu",  # Default to invest4edu for backward compatibility
    blur_funds: bool = False  # Default to not blur the funds
):
    """
    Accept a JSON file and generate a PDF using the specified template.
    
    Parameters:
    - data_file: JSON file containing the data for the report
    - template: Template to use ('invest4edu' or 'investvalue')
    - blur_funds: Whether to blur fund names in the generated PDF
    
    Returns:
    - Generated PDF file
    """
    # Validate template parameter
    template = template.lower()
    if template not in ["invest4edu", "investvalue"]:
        return JSONResponse({"error": "Invalid template. Must be 'invest4edu' or 'investvalue'"}, status_code=400)
    
    # Save the uploaded JSON
    json_filename = f"input_{uuid.uuid4().hex}.json"
    json_path = os.path.join(UPLOAD_DIR, json_filename)
    with open(json_path, "wb") as buffer:
        shutil.copyfileobj(data_file.file, buffer)

    # Load data and check
    data = load_json_data(json_path)
    if not data:
        return JSONResponse({"error": "Invalid JSON data."}, status_code=400)
        
    # Add blur_funds parameter to the data for template use
    data["blur_funds"] = blur_funds

    # Generate HTML using the specific template
    html_filename = f"report_{uuid.uuid4().hex}.html"
    html_path = os.path.join(OUTPUT_DIR, html_filename)
    
    # Set template files based on the selected template
    template_map = {
        "invest4edu": "invest4edu_report.html",
        "investvalue": "investvalue_report.html"
    }
    template_name = template_map[template]
    
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

    output_filename = f"{template}_report_output.pdf"
    return FileResponse(pdf_path, media_type="application/pdf", filename=output_filename)

from fastapi import Body

@app.post("/generate-pdf-json/")
async def generate_pdf_from_json_body(
    data: dict = Body(..., example={
        "clientname": "Akhilesh Gupta",
        "report_title": "Investment Report",
        "logo_url": "",
        "investment_products": {"target": "1.00Cr"},
        "template": "invest4edu",  # or "investvalue"
        "blur_funds": False  # Whether to blur fund names
        # ... (rest of your sample_data.json structure)
    })
):
    """
    Accept JSON data in the request body and generate a PDF using the specified template.
    
    Parameters in JSON body:
    - template: (optional) Template to use ('invest4edu' or 'investvalue'). Defaults to 'invest4edu'.
    - blur_funds: (optional) Whether to blur fund names in the generated PDF. Defaults to False.
    - Other fields: Data to populate the template
    
    Returns:
    - Generated PDF file
    """
    # Extract template and blur_funds parameters from data or use defaults
    template = data.pop("template", "invest4edu").lower()
    blur_funds = data.pop("blur_funds", False)
    
    if template not in ["invest4edu", "investvalue"]:
        return JSONResponse({"error": "Invalid template. Must be 'invest4edu' or 'investvalue'"}, status_code=400)
        
    # Add blur_funds back to the data for template use
    data["blur_funds"] = blur_funds
    
    # Save JSON to a temp file for compatibility
    json_filename = f"input_{uuid.uuid4().hex}.json"
    json_path = os.path.join(UPLOAD_DIR, json_filename)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Generate HTML using the specific template
    html_filename = f"report_{uuid.uuid4().hex}.html"
    html_path = os.path.join(OUTPUT_DIR, html_filename)
    
    # Set template files based on the selected template
    template_map = {
        "invest4edu": "invest4edu_report.html",
        "investvalue": "investvalue_report.html"
    }
    template_name = template_map[template]
    
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

    output_filename = f"{template}_report_output.pdf"
    return FileResponse(pdf_path, media_type="application/pdf", filename=output_filename)

@app.get("/")
def root():
    return HTMLResponse("""
    <h2>Proposal PDF Generator API</h2>
    <p>This API generates PDF reports using different templates based on the input data.</p>
    
    <h3>Endpoints:</h3>
    <ul>
        <li><strong>POST /generate-pdf/</strong> - Upload a JSON file to generate a PDF</li>
        <li><strong>POST /generate-pdf-json/</strong> - Send JSON data in the request body to generate a PDF</li>
    </ul>
    
    <h3>Usage:</h3>
    <h4>1. File Upload (multipart/form-data):</h4>
    <pre>
    curl -X POST \
      -F "data_file=@path/to/your/data.json" \
      -F "template=investvalue" \
      -F "blur_funds=true" \
      http://localhost:8000/generate-pdf/
    </pre>
    
    <h4>2. JSON Body (application/json):</h4>
    <pre>
    curl -X POST \
      -H "Content-Type: application/json" \
      -d '{"clientname":"John Doe", "template":"investvalue", "blur_funds": true, ...}' \
      http://localhost:8000/generate-pdf-json/
    </pre>
    
    <h3>Options:</h3>
    <ul>
        <li><strong>Template Options:</strong>
            <ul>
                <li><code>invest4edu</code> - Default template for Invest4Edu</li>
                <li><code>investvalue</code> - Template for InvestValue</li>
            </ul>
        </li>
        <li><strong>Fund Blurring:</strong>
            <ul>
                <li><code>blur_funds=true</code> - Blur all fund names in the report for confidentiality</li>
                <li><code>blur_funds=false</code> - Show fund names normally (default)</li>
            </ul>
        </li>
    </ul>
    
    <h3>Notes:</h3>
    <ul>
        <li>If no template is specified, the API will use 'invest4edu' as the default template.</li>
        <li>Fund blurring is useful for presentations where specific fund names should not be visible.</li>
    </ul>
    """)