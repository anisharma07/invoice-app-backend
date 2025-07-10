#!/usr/bin/env python3
"""
Test script for HTML to PDF API
Demonstrates all the available endpoints and functionality
"""

import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:8888"
PDF_API_URL = f"{BASE_URL}/pdf"

# Sample HTML content for testing
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Document</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        .content { margin: 20px 0; }
        .highlight { background-color: #f0f0f0; padding: 10px; }
    </style>
</head>
<body>
    <h1>Sample PDF Document</h1>
    <div class="content">
        <p>This is a test document generated from HTML content.</p>
        <div class="highlight">
            <p>This is a highlighted section.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
                <li>Item 3</li>
            </ul>
        </div>
    </div>
    <p>Generated on: <span id="date"></span></p>
    <script>
        document.getElementById('date').textContent = new Date().toLocaleDateString();
    </script>
</body>
</html>
"""


def test_health_check():
    """Test the main health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_pdf_generation_from_html():
    """Test PDF generation from direct HTML content"""
    print("\n📄 Testing PDF generation from HTML content...")

    payload = {
        "user_id": "test_user_123",
        "html_content": SAMPLE_HTML,
        "filename": "test_document.pdf",
        "options": {
            "page-size": "A4",
            "margin-top": "1in",
            "margin-bottom": "1in"
        }
    }

    try:
        response = requests.post(f"{PDF_API_URL}/generate", json=payload)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")

        if response.status_code == 200:
            return result.get('file_id')
        return None
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        return None


def test_pdf_generation_from_url():
    """Test PDF generation from URL"""
    print("\n🌐 Testing PDF generation from URL...")

    payload = {
        "user_id": "test_user_123",
        "url": "https://httpbin.org/html",
        "filename": "webpage_test.pdf"
    }

    try:
        response = requests.post(f"{PDF_API_URL}/generate", json=payload)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")

        if response.status_code == 200:
            return result.get('file_id')
        return None
    except Exception as e:
        print(f"❌ URL PDF generation failed: {e}")
        return None


def test_pdf_preview():
    """Test PDF preview functionality"""
    print("\n👁️ Testing PDF preview...")

    payload = {
        "html_content": SAMPLE_HTML,
        "options": {
            "page-size": "A4"
        }
    }

    try:
        response = requests.post(f"{PDF_API_URL}/preview", json=payload)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ PDF preview generated successfully")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Content-Length: {len(response.content)} bytes")

            # Optionally save the preview
            with open("preview_test.pdf", "wb") as f:
                f.write(response.content)
            print("💾 Preview saved as 'preview_test.pdf'")
            return True
        else:
            print(f"❌ Preview failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Preview failed: {e}")
        return False


def test_list_user_pdfs():
    """Test listing user PDFs"""
    print("\n📋 Testing PDF list...")

    try:
        response = requests.get(f"{PDF_API_URL}/list/test_user_123")
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ List PDFs failed: {e}")
        return False


def test_download_pdf(file_id):
    """Test PDF download"""
    if not file_id:
        print("\n⏭️ Skipping download test - no file ID available")
        return False

    print(f"\n⬇️ Testing PDF download for file ID: {file_id}")

    try:
        response = requests.get(f"{PDF_API_URL}/download/{file_id}")
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ PDF downloaded successfully")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Content-Length: {len(response.content)} bytes")

            # Save the downloaded file
            filename = f"downloaded_pdf_{file_id}.pdf"
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"💾 File saved as '{filename}'")
            return True
        else:
            print(f"❌ Download failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False


def test_delete_pdf(file_id):
    """Test PDF deletion"""
    if not file_id:
        print("\n⏭️ Skipping delete test - no file ID available")
        return False

    print(f"\n🗑️ Testing PDF deletion for file ID: {file_id}")

    try:
        response = requests.delete(f"{PDF_API_URL}/delete/{file_id}")
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Delete failed: {e}")
        return False


def test_file_upload_html():
    """Test PDF generation from HTML file upload"""
    print("\n📁 Testing PDF generation from HTML file upload...")

    # Create a temporary HTML file
    html_file_content = SAMPLE_HTML
    temp_filename = "temp_test.html"

    with open(temp_filename, "w", encoding="utf-8") as f:
        f.write(html_file_content)

    try:
        with open(temp_filename, "rb") as f:
            files = {"file": (temp_filename, f, "text/html")}
            data = {"user_id": "test_user_123"}

            response = requests.post(
                f"{PDF_API_URL}/generate", files=files, data=data)
            print(f"Status: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")

            if response.status_code == 200:
                return result.get('file_id')
            return None
    except Exception as e:
        print(f"❌ File upload PDF generation failed: {e}")
        return None
    finally:
        # Clean up temporary file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


def run_all_tests():
    """Run all tests"""
    print("🚀 Starting HTML to PDF API Tests")
    print("=" * 50)

    # Test health check first
    if not test_health_check():
        print("❌ Server appears to be down. Please start the server first.")
        return

    # Test PDF generation from HTML
    file_id_1 = test_pdf_generation_from_html()

    # Test PDF generation from URL (might fail if no internet)
    file_id_2 = test_pdf_generation_from_url()

    # Test file upload
    file_id_3 = test_file_upload_html()

    # Test preview
    test_pdf_preview()

    # Test listing
    test_list_user_pdfs()

    # Test download (use the first successful file ID)
    test_file_id = file_id_1 or file_id_2 or file_id_3
    test_download_pdf(test_file_id)

    # Test delete (use a different file ID if available)
    delete_file_id = file_id_2 or file_id_3
    test_delete_pdf(delete_file_id)

    print("\n" + "=" * 50)
    print("🏁 Tests completed!")
    print("\nGenerated files:")
    print("- preview_test.pdf (from preview test)")
    if test_file_id:
        print(f"- downloaded_pdf_{test_file_id}.pdf (from download test)")


if __name__ == "__main__":
    run_all_tests()
