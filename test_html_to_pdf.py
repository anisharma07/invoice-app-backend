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
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{PDF_API_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_convert_html_to_pdf():
    """Test PDF conversion from direct HTML content"""
    print("\n📄 Testing PDF conversion from HTML content...")

    payload = {
        "html_content": SAMPLE_HTML,
        "filename": "test_document.pdf",
        "options": {
            "page-size": "A4",
            "margin-top": "1in",
            "margin-bottom": "1in"
        }
    }

    try:
        response = requests.post(f"{PDF_API_URL}/convert", json=payload)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ PDF conversion successful")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Content-Length: {len(response.content)} bytes")

            # Save the PDF file
            filename = "converted_test.pdf"
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"💾 PDF saved as '{filename}'")
            return True
        else:
            print(f"❌ Conversion failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ PDF conversion failed: {e}")
        return False


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

            # Save the preview
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


def test_file_upload_html():
    """Test PDF conversion from HTML file upload"""
    print("\n� Testing PDF conversion from HTML file upload...")

    # Create a temporary HTML file
    temp_filename = "temp_test.html"

    with open(temp_filename, "w", encoding="utf-8") as f:
        f.write(SAMPLE_HTML)

    try:
        with open(temp_filename, "rb") as f:
            files = {"file": (temp_filename, f, "text/html")}

            response = requests.post(f"{PDF_API_URL}/convert", files=files)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                print("✅ File upload PDF conversion successful")
                print(f"Content-Type: {response.headers.get('Content-Type')}")
                print(f"Content-Length: {len(response.content)} bytes")

                # Save the PDF file
                filename = "uploaded_file_test.pdf"
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"💾 PDF saved as '{filename}'")
                return True
            else:
                print(f"❌ File upload conversion failed: {response.text}")
                return False
    except Exception as e:
        print(f"❌ File upload PDF conversion failed: {e}")
        return False
    finally:
        # Clean up temporary file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


def test_custom_options():
    """Test PDF conversion with custom options"""
    print("\n⚙️ Testing PDF conversion with custom options...")

    payload = {
        "html_content": SAMPLE_HTML,
        "filename": "custom_options_test.pdf",
        "options": {
            "page-size": "Letter",
            "orientation": "Landscape",
            "margin-top": "2in",
            "margin-bottom": "2in",
            "margin-left": "1.5in",
            "margin-right": "1.5in",
            "zoom": "1.2"
        }
    }

    try:
        response = requests.post(f"{PDF_API_URL}/convert", json=payload)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ Custom options PDF conversion successful")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Content-Length: {len(response.content)} bytes")

            # Save the PDF file
            filename = "custom_options_test.pdf"
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"💾 PDF saved as '{filename}'")
            return True
        else:
            print(f"❌ Custom options conversion failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Custom options PDF conversion failed: {e}")
        return False


def test_error_cases():
    """Test various error cases"""
    print("\n❌ Testing error cases...")

    # Test empty request
    print("  Testing empty request...")
    try:
        response = requests.post(f"{PDF_API_URL}/convert", json={})
        print(f"  Status: {response.status_code}")
        if response.status_code == 400:
            print("  ✅ Empty request handled correctly")
        else:
            print(f"  ❌ Unexpected response: {response.text}")
    except Exception as e:
        print(f"  ❌ Error test failed: {e}")

    # Test invalid HTML
    print("  Testing invalid HTML...")
    try:
        response = requests.post(f"{PDF_API_URL}/convert", json={
            "html_content": "<invalid><html><missing></tags>"
        })
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print("  ✅ Invalid HTML handled gracefully (cleaned by BeautifulSoup)")
        else:
            print(f"  ❌ Unexpected response: {response.text}")
    except Exception as e:
        print(f"  ❌ Error test failed: {e}")


def run_all_tests():
    """Run all tests"""
    print("🚀 Starting HTML to PDF API Tests")
    print("=" * 50)

    # Test health check first
    if not test_health_check():
        print("❌ Health check failed. Please check if the server is running.")
        print("Start the server with: python server.py")
        return

    # Test basic conversion
    test_convert_html_to_pdf()

    # Test preview
    test_pdf_preview()

    # Test file upload
    test_file_upload_html()

    # Test custom options
    test_custom_options()

    # Test error cases
    test_error_cases()

    print("\n" + "=" * 50)
    print("🏁 Tests completed!")
    print("\nGenerated files:")
    print("- converted_test.pdf (from basic conversion)")
    print("- preview_test.pdf (from preview test)")
    print("- uploaded_file_test.pdf (from file upload test)")
    print("- custom_options_test.pdf (from custom options test)")


if __name__ == "__main__":
    run_all_tests()
