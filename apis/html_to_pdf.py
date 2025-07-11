from flask import Blueprint, request, jsonify, send_file
import pdfkit
from bs4 import BeautifulSoup
import io
import os
import subprocess
from datetime import datetime

html_to_pdf_bp = Blueprint('html_to_pdf', __name__)


# Configure wkhtmltopdf path and options
def get_wkhtmltopdf_config():
    """Get wkhtmltopdf configuration based on environment"""
    try:
        # Try to find wkhtmltopdf executable
        result = subprocess.run(['which', 'wkhtmltopdf'], capture_output=True, text=True)
        if result.returncode == 0:
            wkhtmltopdf_path = result.stdout.strip()
        else:
            # Common paths to check
            common_paths = [
                '/usr/bin/wkhtmltopdf',
                '/usr/local/bin/wkhtmltopdf',
                '/opt/wkhtmltopdf/bin/wkhtmltopdf'
            ]
            wkhtmltopdf_path = None
            for path in common_paths:
                if os.path.exists(path):
                    wkhtmltopdf_path = path
                    break
        
        # Configure pdfkit
        if wkhtmltopdf_path:
            config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        else:
            config = None
            
        return config
    except Exception:
        return None

# PDF generation options
PDF_OPTIONS = {
    'page-size': 'A4',
    'margin-top': '0.75in',
    'margin-right': '0.75in',
    'margin-bottom': '0.75in',
    'margin-left': '0.75in',
    'encoding': "UTF-8",
    'no-outline': None,
    'enable-local-file-access': None,
    'disable-smart-shrinking': '',
    'print-media-type': '',
    'disable-javascript': ''
}


@html_to_pdf_bp.route('/convert', methods=['POST'])
def convert_html_to_pdf():
    """
    Convert HTML content to PDF and return the PDF file directly.
    Accepts HTML content in the request body and returns PDF.
    """
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
             body {{
                margin: 0;
                padding: 5px 10px;
                font-family: Arial, sans-serif;
                font-size: 10px;
            }}
            .footer-container {{
                width: 100%;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .footer-left {{
                text-align: left;
            }}
            .footer-right {{
                text-align: right;
            }}
        </style>
    </head>
    <body>
        <div style="text-align: left;">{current_datetime}</div>
   
    """

    footer_html = """
        
    </body>
    </html>
    """
    try:
        # Check if request contains JSON data
        if request.is_json:
            data = request.get_json()
            if not data or 'html_content' not in data:
                return jsonify({"error": "html_content is required in JSON body"}), 400
            html_content = header_html + data['html_content'] + footer_html
            filename = data.get('filename', 'document.pdf')
            custom_options = data.get('options', {})
        
        # Check if HTML file was uploaded
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            if not file.filename.lower().endswith(('.html', '.htm')):
                return jsonify({"error": "Only HTML files are allowed"}), 400
            
            html_content = file.read().decode('utf-8')
            filename = file.filename.rsplit('.', 1)[0] + '.pdf'
            custom_options = {}
        
        else:
            return jsonify({
                "error": "Provide HTML content in JSON body with 'html_content' field or upload an HTML file"
            }), 400

        # Clean and validate HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        cleaned_html = str(soup)

        # Merge custom options with default PDF options
        pdf_options = {**PDF_OPTIONS, **custom_options}

        # Generate PDF
        try:
            config = get_wkhtmltopdf_config()
            if config is None:
                return jsonify({
                    "error": "wkhtmltopdf not found. Please ensure wkhtmltopdf is installed and accessible."
                }), 500
                
            pdf_data = pdfkit.from_string(cleaned_html, False, options=pdf_options, configuration=config)
        except Exception as e:
            return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500

        # Return PDF file directly
        return send_file(
            io.BytesIO(pdf_data),
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500


@html_to_pdf_bp.route('/preview', methods=['POST'])
def preview_pdf():
    """
    Generate and return PDF for preview (inline display) without download.
    """
    try:
        data = request.get_json()

        if not data or 'html_content' not in data:
            return jsonify({"error": "html_content is required"}), 400

        html_content = data['html_content']

        # Clean HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        cleaned_html = str(soup)

        # Get custom options
        custom_options = data.get('options', {})
        pdf_options = {**PDF_OPTIONS, **custom_options}

        # Generate PDF
        try:
            config = get_wkhtmltopdf_config()
            if config is None:
                return jsonify({
                    "error": "wkhtmltopdf not found. Please ensure wkhtmltopdf is installed and accessible."
                }), 500
                
            pdf_data = pdfkit.from_string(cleaned_html, False, options=pdf_options, configuration=config)
        except Exception as e:
            return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500

        # Return PDF for inline display
        return send_file(
            io.BytesIO(pdf_data),
            as_attachment=False,
            download_name='preview.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({"error": f"Preview generation failed: {str(e)}"}), 500


@html_to_pdf_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    try:
        # Check if wkhtmltopdf is available
        config = get_wkhtmltopdf_config()
        if config is None:
            return jsonify({
                "status": "unhealthy",
                "error": "wkhtmltopdf executable not found"
            }), 500
        
        # Test if pdfkit is working
        test_html = "<html><body><h1>Test</h1></body></html>"
        pdfkit.from_string(test_html, False, options={'page-size': 'A4'}, configuration=config)
        
        return jsonify({
            "status": "healthy",
            "service": "HTML to PDF Converter",
            "message": "Service is running and PDF generation is working"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500
