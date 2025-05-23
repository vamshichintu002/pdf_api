import json
import os
import sys
import argparse
import webbrowser
from jinja2 import Environment, FileSystemLoader

class BrowserPDFGenerator:
    """Generate HTML reports that can be printed to PDF using the browser."""
    
    def __init__(self, template_dir='templates'):
        """Initialize the generator with template directory."""
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
    def generate_html(self, template_name, data, output_path):
        """Generate HTML from template and data."""
        try:
            # Get the template
            template = self.env.get_template(template_name)
            # Render the template with the original data (nested structure)
            html_content = template.render(**data)
            # Write the HTML to a file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return output_path
        except Exception as e:
            print(f"Error generating HTML: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _prepare_template_data(self, data):
        """Prepare data for the template in a simplified format."""
        template_data = {
            'report_title': data.get('report_title', 'Investment Report'),
            'target': data.get('investment_products', {}).get('target', '1.00Cr'),
            'points': [],
            'funds': [],
            'allocation_description': '',
            'benefits': [],
            'equity_percent': 70,
            'debt_percent': 30,
            'allocation_items': [],
            'total_amount': '0.00 Cr.'
        }
        
        # Extract mutual fund points
        mutual_fund = data.get('investment_products', {}).get('mutual_fund', {})
        if mutual_fund and 'points' in mutual_fund:
            template_data['points'] = mutual_fund['points']
        
        # Extract top funds
        if mutual_fund and 'top_funds' in mutual_fund:
            for fund in mutual_fund['top_funds']:
                template_data['funds'].append({
                    'name': fund.get('name', ''),
                    'category': fund.get('category', ''),
                    'one_year': fund.get('returns', {}).get('one_year', 0),
                    'three_years': fund.get('returns', {}).get('three_years', 0),
                    'five_years': fund.get('returns', {}).get('five_years', 0)
                })
        
        # Extract asset allocation data
        asset_allocation = data.get('asset_allocation', {})
        if asset_allocation:
            template_data['allocation_description'] = asset_allocation.get('description', '')
            template_data['benefits'] = asset_allocation.get('benefits', [])
            
            # Extract distribution
            distribution = asset_allocation.get('distribution', {})
            if distribution:
                template_data['equity_percent'] = distribution.get('equity', 70)
                template_data['debt_percent'] = distribution.get('debt', 30)
            
            # Extract allocation items
            template_data['allocation_items'] = asset_allocation.get('items', [])
            template_data['total_amount'] = asset_allocation.get('total', '0.00 Cr.')
        
        return template_data
    
    def open_in_browser(self, html_path):
        """Open the HTML file in the default browser."""
        try:
            abs_path = os.path.abspath(html_path)
            webbrowser.open('file://' + abs_path)
            return abs_path
        except Exception as e:
            print(f"Error opening browser: {str(e)}")
            return None
    
    def create_report(self, json_data_path, template_name='simple_report.html', 
                      output_name='output_report', open_html=True):
        """Create a report from JSON data and open in browser for PDF printing."""
        # Load data
        data = load_json_data(json_data_path)
        if not data:
            return False
            
        # Set output path
        html_path = f"{output_name}.html"
        
        # Generate HTML
        html_output = self.generate_html(template_name, data, html_path)
        if not html_output:
            return False
            
        print(f"HTML report generated successfully: {os.path.abspath(html_output)}")
        
        # Open in browser if requested
        if open_html:
            self.open_in_browser(html_output)
            
            # Print instructions for PDF conversion
            print("\nTo convert the HTML to PDF:")
            print("1. The HTML report should now be open in your default browser")
            print("2. Press Ctrl+P to open the print dialog")
            print("3. Select 'Save as PDF' as the destination")
            print("4. Click 'Save' to generate the PDF")
            print("\nTip: For best results, use Chrome or Edge browser for PDF generation")
        
        return True


def load_json_data(file_path):
    """Load data from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {str(e)}")
        return None
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return None


def generate_pdf_with_playwright(html_path, pdf_path):
    """Generate a PDF from the HTML file using Playwright (sync version for Windows)."""
    try:
        # Define absolute paths first
        abs_html_path = os.path.abspath(html_path)
        abs_pdf_path = os.path.abspath(pdf_path)
        # Use subprocess to run a separate Python process with script for PDF generation
        # This avoids the asyncio event loop issues on Windows
        import subprocess
        import sys
        
        # Create a small Python script to generate PDF
        script_content = f"""
import os
from playwright.sync_api import sync_playwright
import time

abs_html_path = r"{os.path.abspath(html_path)}"
abs_pdf_path = r"{os.path.abspath(pdf_path)}"
file_url = f"file:///{abs_html_path.replace(os.sep, '/')}"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(file_url)
    # Wait for page to render
    time.sleep(1)
    page.pdf(
        path=abs_pdf_path,
        format="A4",
        margin={{"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"}},
        print_background=True,
        display_header_footer=False
    )
    browser.close()
print(f"PDF generated at: {{abs_pdf_path}}")
"""
        # Save the script to a temporary file
        script_path = os.path.join(os.path.dirname(html_path), "_temp_pdf_generator.py")
        with open(script_path, 'w') as script_file:
            script_file.write(script_content)
        
        # Run the script in a separate process
        result = subprocess.run([sys.executable, script_path], 
                               capture_output=True, text=True, check=False)
        
        # Clean up the temporary script
        try:
            os.remove(script_path)
        except:
            pass
        
        if result.returncode != 0:
            print(f"PDF generation error: {result.stderr}")
            return False
        
        print(result.stdout)
        return os.path.exists(pdf_path)
    
    except ImportError:
        print("Playwright is not installed. Please run 'pip install playwright' and 'playwright install' to use PDF generation.")
        return False
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return False


async def generate_pdf_with_playwright_async(html_path, pdf_path):
    """Generate a PDF from the HTML file using Playwright (async version for FastAPI)."""
    try:
        # Define absolute paths first
        abs_html_path = os.path.abspath(html_path)
        abs_pdf_path = os.path.abspath(pdf_path)
        
        # Import necessary modules
        import subprocess
        import sys
        import asyncio
        import tempfile
        from concurrent.futures import ThreadPoolExecutor
        import uuid
        
        # Create a small Python script to generate PDF - use a unique name to avoid reload issues
        script_content = f"""
import os
import sys
try:
    from playwright.sync_api import sync_playwright
    import time

    abs_html_path = r"{os.path.abspath(html_path)}"
    abs_pdf_path = r"{os.path.abspath(pdf_path)}"
    file_url = f"file:///{abs_html_path.replace(os.sep, '/')}"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(file_url)
        # Wait for page to render
        time.sleep(1)
        page.pdf(
            path=abs_pdf_path,
            format="A4",
            margin={{"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"}},
            print_background=True,
            display_header_footer=False
        )
        browser.close()
    print(f"PDF generated at: {{abs_pdf_path}}")
    sys.exit(0)
except Exception as e:
    print(f"Error in PDF generation script: {{str(e)}}")
    sys.exit(1)
"""
        # Create a temporary directory that won't be watched by StatReload
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(html_path)), 'temp_scripts')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Use a unique filename for each generation to avoid conflicts
        unique_id = uuid.uuid4().hex
        script_path = os.path.join(temp_dir, f"pdf_generator_{unique_id}.py")
        
        with open(script_path, 'w') as script_file:
            script_file.write(script_content)
        
        # Function to run subprocess in a thread
        def run_subprocess():
            try:
                result = subprocess.run(
                    [sys.executable, script_path],
                    capture_output=True, 
                    text=True, 
                    check=False,
                    timeout=30  # Add timeout to prevent hanging
                )
                
                # Always clean up the temporary script
                try:
                    os.remove(script_path)
                except Exception as e:
                    print(f"Warning: Could not remove temp script: {e}")
                
                if result.returncode != 0:
                    print(f"PDF generation error: {result.stderr}")
                    return False
                
                print(result.stdout)
                return os.path.exists(pdf_path)
            except subprocess.TimeoutExpired:
                print("PDF generation timed out after 30 seconds")
                return False
            except Exception as e:
                print(f"Unexpected error in subprocess: {str(e)}")
                return False
        
        # Run subprocess in a separate thread to avoid blocking the event loop
        with ThreadPoolExecutor() as executor:
            return await asyncio.get_event_loop().run_in_executor(executor, run_subprocess)
    
    except ImportError:
        print("Playwright is not installed. Please run 'pip install playwright' and 'playwright install' to use PDF generation.")
        return False
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return False


def main():
    """Command line interface for the browser-based PDF generator."""
    parser = argparse.ArgumentParser(description='Generate HTML reports that can be printed to PDF using the browser.')
    parser.add_argument('--data', '-d', default='sample_data.json', help='Path to the JSON data file')
    parser.add_argument('--template', '-t', default='simple_report.html', 
                        help='Name of the HTML template file (must be in the templates directory)')
    parser.add_argument('--output', '-o', default='output_report', help='Base name for output files (without extension)')
    parser.add_argument('--no-open', action='store_true', help='Do not open the generated HTML in browser')
    parser.add_argument('--no-pdf', action='store_true', help='Do not generate PDF using Playwright')
    
    args = parser.parse_args()
    
    # Check if the data file exists
    if not os.path.exists(args.data):
        print(f"Error: Data file '{args.data}' not found.")
        sys.exit(1)
    
    # Check if the template exists
    template_path = os.path.join('templates', args.template)
    if not os.path.exists(template_path):
        print(f"Error: Template file '{template_path}' not found.")
        sys.exit(1)
    
    # Generate the report
    generator = BrowserPDFGenerator()
    success = generator.create_report(
        args.data, 
        args.template, 
        args.output, 
        not args.no_open
    )
    
    # Generate PDF if requested
    if success and not args.no_pdf:
        html_file = f"{args.output}.html"
        pdf_file = f"{args.output}.pdf"
        generate_pdf_with_playwright(html_file, pdf_file)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()