# Investment Proposal PDF Generator API

This project provides a REST API for generating professional PDF investment reports based on JSON data. The system produces dynamic PDF reports using customizable HTML templates.

## Features

- REST API with FastAPI for PDF generation
- Dynamic PDF generation from JSON data
- Multiple template support (invest4edu, investvalue)
- Fund name blurring option for confidentiality
- Professional styling with CSS
- Playwright-based PDF generation for consistent results
- CORS support for cross-origin requests

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. For PDF generation functionality (required):
   - Install Playwright: `pip install playwright`
   - Install the browsers: `playwright install`

## Usage

### Starting the API Server

Run the FastAPI server:

```bash
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### 1. Generate PDF from JSON File Upload

**Endpoint:** `POST /generate-pdf/`

**Parameters:**
- `data_file`: JSON file containing the data for the report (form data)
- `template`: Template to use (`invest4edu` or `investvalue`, defaults to `invest4edu`)
- `blur_funds`: Whether to blur fund names in the generated PDF (defaults to `false`)

**Example (using curl):**
```bash
curl -X POST \
  -F "data_file=@sample_data.json" \
  -F "template=investvalue" \
  -F "blur_funds=true" \
  http://localhost:8000/generate-pdf/
```

#### 2. Generate PDF from JSON Body

**Endpoint:** `POST /generate-pdf-json/`

**Parameters:**
- Request body: JSON data containing template data
- `template`: Template to use (`invest4edu` or `investvalue`, defaults to `invest4edu`)
- `blur_funds`: Whether to blur fund names in the generated PDF (defaults to `false`)

**Example (using curl):**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"clientname":"John Doe", "template":"investvalue", "blur_funds": true, ...}' \
  http://localhost:8000/generate-pdf-json/
```

### Interactive Documentation

FastAPI provides automatic interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## JSON Data Structure

The JSON data should follow this structure:

```json
{
  "clientname": "Client Name",
  "report_title": "Investment Report",
  "logo_url": "",
  "template": "invest4edu",  // Optional: "invest4edu" or "investvalue"
  "blur_funds": false,       // Optional: Whether to blur fund names
  "investment_products": {
    "target": "1.00Cr",
    "mutual_fund": {
      "points": ["Point 1", "Point 2", ...],
      "top_funds": [
        {
          "name": "Fund Name",
          "category": "Category",
          "returns": {
            "one_year": 8.00,
            "three_years": 8.00,
            "five_years": 8.00
          }
        }
      ]
    }
  },
  "asset_allocation": {
    "description": "Description text",
    "benefits": ["Benefit 1", "Benefit 2", ...],
    "distribution": {
      "equity": 70,
      "debt": 30
    },
    "items": [
      {
        "name": "Item name",
        "details": ["Detail 1", "Detail 2", ...],
        "asset_class": "Asset class",
        "amount": "Amount"
      }
    ],
    "total": "Total amount"
  },
  "fixed_income_offering": {
    "target": "1.00Cr",
    "description": "Description text",
    "bullets": ["Point 1", "Point 2", ...],
    "debt_papers": [
      {
        "fund_name": "Fund Name",
        "maturity": "Maturity Date",
        "payment_frequency": "Payment Frequency",
        "ytm": "Yield to Maturity",
        "quantum": "Quantum",
        "type": "Type",
        "face_value": "Face Value",
        "rating": "Rating"
      }
    ]
  },
  "pms": {
    "target": "1.00Cr",
    "description": "Description text",
    "bullets": ["Point 1", "Point 2", ...],
    "funds": ["Fund details"]
  },
  "private_equity": {
    "target": "1.00Cr",
    "description": "Description text",
    "bullets": ["Point 1", "Point 2", ...],
    "scrips": ["Scrip details"]
  }
}
```

See `sample_data.json` for a complete example.

## Templates and Custom Reports

The system currently supports two report templates:

1. **invest4edu** - The default template for Invest4Edu reports
2. **investvalue** - An alternative template for InvestValue reports

To create custom reports:

1. Create a new HTML template in the `templates` directory
2. Update the template mapping in `app.py`
3. Prepare your JSON data file with the appropriate structure
4. Call the API with your custom template parameter

## Fund Name Blurring

The API supports blurring fund names in the generated PDFs for confidentiality purposes. To enable this feature:

- When uploading a JSON file: Set the `blur_funds` parameter to `true`
- When sending JSON in the request body: Include `"blur_funds": true` in your JSON data

## Project Files

- `app.py`: Main FastAPI application with API endpoints
- `browser_pdf_generator.py`: PDF generation functionality using Playwright
- `templates/invest4edu_report.html`: Template for Invest4Edu reports
- `templates/investvalue_report.html`: Template for InvestValue reports
- `sample_data.json`: Example data structure with template and blur_funds parameters
- `requirements.txt`: Project dependencies

## Directory Structure

- `uploads/`: Temporary storage for uploaded JSON files
- `outputs/`: Generated HTML and PDF files
- `templates/`: HTML templates for report generation

## PDF Generation

The API uses Playwright for PDF generation, which provides consistent and high-quality results. Playwright renders the HTML using a headless browser and then generates a PDF, ensuring that complex CSS layouts and styling are correctly applied.
