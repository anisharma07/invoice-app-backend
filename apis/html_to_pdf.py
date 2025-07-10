from flask import Blueprint, request, jsonify, send_file
import pdfkit
import uuid
import tempfile
import os
import requests
from bs4 import BeautifulSoup
from services.s3 import s3_client, BUCKET_NAME
from services.database import cursor, conn
from utils.validators import validate_url
import io

html_to_pdf_bp = Blueprint('html_to_pdf', __name__)

# PDF generation options
PDF_OPTIONS = {
    'page-size': 'A4',
    'margin-top': '0.75in',
    'margin-right': '0.75in',
    'margin-bottom': '0.75in',
    'margin-left': '0.75in',
    'encoding': "UTF-8",
    'no-outline': None,
    'enable-local-file-access': None
}


@html_to_pdf_bp.route('/generate', methods=['POST'])
def generate_pdf():
    """
    Generate PDF from HTML content
    Supports multiple input methods:
    1. Direct HTML content
    2. URL to fetch HTML from
    3. File upload containing HTML
    """
    try:
        data = request.get_json() if request.is_json else {}

        # Get user_id for file storage
        user_id = data.get('user_id') or request.form.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        # Get HTML content from different sources
        html_content = None
        source_type = None
        filename = None

        # Method 1: Direct HTML content
        if 'html_content' in data:
            html_content = data['html_content']
            source_type = 'direct'
            filename = data.get('filename', 'generated_document.pdf')

        # Method 2: URL to fetch HTML from
        elif 'url' in data:
            url = data['url']
            if not validate_url(url):
                return jsonify({"error": "Invalid URL provided"}), 400

            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                html_content = response.text
                source_type = 'url'
                filename = data.get(
                    'filename', f'webpage_{uuid.uuid4().hex[:8]}.pdf')
            except requests.RequestException as e:
                return jsonify({"error": f"Failed to fetch URL: {str(e)}"}), 400

        # Method 3: HTML file upload
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400

            if not file.filename.lower().endswith(('.html', '.htm')):
                return jsonify({"error": "Only HTML files are allowed"}), 400

            html_content = file.read().decode('utf-8')
            source_type = 'file'
            filename = file.filename.rsplit('.', 1)[0] + '.pdf'

        if not html_content:
            return jsonify({
                "error": "No HTML content provided. Use 'html_content', 'url', or upload an HTML file."
            }), 400

        # Clean and validate HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        cleaned_html = str(soup)

        # Get custom options if provided
        custom_options = data.get('options', {})
        pdf_options = {**PDF_OPTIONS, **custom_options}

        # Generate PDF
        try:
            pdf_data = pdfkit.from_string(
                cleaned_html, False, options=pdf_options)
        except Exception as e:
            return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500

        # Upload to S3
        unique_filename = f"{uuid.uuid4()}-{filename}"
        s3_key = f"user_{user_id}/pdfs/{unique_filename}"

        try:
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=pdf_data,
                ContentType='application/pdf'
            )
        except Exception as e:
            return jsonify({"error": f"Failed to upload PDF to storage: {str(e)}"}), 500

        # Save metadata to database
        try:
            cursor.execute(
                """INSERT INTO user_files (user_id, filename, s3_key, file_type, source_type, original_content) 
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (user_id, filename, unique_filename, 'pdf', source_type,
                 data.get('url', '') if source_type == 'url' else '')
            )
            result = cursor.fetchone()
            if result:
                conn.commit()
                file_id = result['id']
            else:
                return jsonify({"error": "Failed to save file metadata"}), 500
        except Exception as e:
            conn.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500

        return jsonify({
            "success": True,
            "file_id": file_id,
            "filename": filename,
            "s3_key": unique_filename,
            "source_type": source_type,
            "size": len(pdf_data),
            "message": "PDF generated and uploaded successfully"
        })

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@html_to_pdf_bp.route('/download/<file_id>', methods=['GET'])
def download_pdf(file_id):
    """Download a generated PDF file"""
    try:
        # Get file metadata from database
        cursor.execute(
            "SELECT filename, s3_key, user_id FROM user_files WHERE id = %s AND file_type = %s",
            (file_id, 'pdf')
        )
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "PDF file not found"}), 404

        filename, s3_key, user_id = result['filename'], result['s3_key'], result['user_id']

        # Download from S3
        s3_object_key = f"user_{user_id}/pdfs/{s3_key}"
        try:
            response = s3_client.get_object(
                Bucket=BUCKET_NAME, Key=s3_object_key)
            pdf_content = response['Body'].read()
        except Exception as e:
            return jsonify({"error": f"Failed to download file from storage: {str(e)}"}), 500

        # Return file
        return send_file(
            io.BytesIO(pdf_content),
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({"error": f"Download failed: {str(e)}"}), 500


@html_to_pdf_bp.route('/preview', methods=['POST'])
def preview_pdf():
    """Generate and return PDF directly without storing"""
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
            pdf_data = pdfkit.from_string(
                cleaned_html, False, options=pdf_options)
        except Exception as e:
            return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500

        # Return PDF directly
        return send_file(
            io.BytesIO(pdf_data),
            as_attachment=False,
            download_name='preview.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({"error": f"Preview generation failed: {str(e)}"}), 500


@html_to_pdf_bp.route('/list/<user_id>', methods=['GET'])
def list_user_pdfs(user_id):
    """List all PDFs generated by a user"""
    try:
        cursor.execute(
            """SELECT id, filename, created_at, source_type, original_content 
               FROM user_files 
               WHERE user_id = %s AND file_type = %s 
               ORDER BY created_at DESC""",
            (user_id, 'pdf')
        )
        results = cursor.fetchall()

        pdfs = []
        for row in results:
            pdfs.append({
                'id': row['id'],
                'filename': row['filename'],
                'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                'source_type': row['source_type'],
                'original_url': row['original_content'] if row['source_type'] == 'url' else None
            })

        return jsonify({
            "success": True,
            "count": len(pdfs),
            "pdfs": pdfs
        })

    except Exception as e:
        return jsonify({"error": f"Failed to list PDFs: {str(e)}"}), 500


@html_to_pdf_bp.route('/delete/<file_id>', methods=['DELETE'])
def delete_pdf(file_id):
    """Delete a PDF file"""
    try:
        # Get file metadata
        cursor.execute(
            "SELECT s3_key, user_id FROM user_files WHERE id = %s AND file_type = %s",
            (file_id, 'pdf')
        )
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "PDF file not found"}), 404

        s3_key, user_id = result['s3_key'], result['user_id']

        # Delete from S3
        s3_object_key = f"user_{user_id}/pdfs/{s3_key}"
        try:
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=s3_object_key)
        except Exception as e:
            return jsonify({"error": f"Failed to delete file from storage: {str(e)}"}), 500

        # Delete from database
        try:
            cursor.execute("DELETE FROM user_files WHERE id = %s", (file_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500

        return jsonify({
            "success": True,
            "message": "PDF deleted successfully"
        })

    except Exception as e:
        return jsonify({"error": f"Delete failed: {str(e)}"}), 500
