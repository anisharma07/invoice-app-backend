#!/usr/bin/env python3
"""
Test script for Logo API endpoints

This script demonstrates how to:
1. Register a user
2. Login to get JWT token
3. Upload a logo
4. Get all logos
5. Get specific logo details
6. Delete a logo

Make sure your Flask server is running before executing this script.
"""

import requests
import json

# Base URL of your Flask application
BASE_URL = "http://localhost:5000"


def test_logo_api():
    """Test the logo API endpoints"""

    # Step 1: Register a test user
    print("📝 Registering a test user...")
    register_data = {
        "name": "Logo Test User",
        "email": "logotest@example.com",
        "password": "testpassword123"
    }

    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    if response.status_code == 201 or response.status_code == 200:
        print("✅ User registered successfully")
    elif response.status_code == 400 and "already exists" in response.text:
        print("ℹ️ User already exists, continuing...")
    else:
        print(f"❌ Failed to register user: {response.text}")
        return

    # Step 2: Login to get JWT token
    print("\n🔐 Logging in...")
    login_data = {
        "email": "logotest@example.com",
        "password": "testpassword123"
    }

    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Failed to login: {response.text}")
        return

    token = response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")

    # Step 3: Upload a logo (simulate with a small text file)
    print("\n📤 Uploading a logo...")

    # Create a dummy image file for testing
    logo_content = b"dummy image content for testing"
    files = {
        'logo': ('test-logo.png', logo_content, 'image/png')
    }

    response = requests.post(f"{BASE_URL}/logos/",
                             files=files, headers=headers)
    if response.status_code == 201:
        logo_data = response.json()
        logo_id = logo_data["logo_id"]
        logo_url = logo_data["logo_url"]
        print(f"✅ Logo uploaded successfully!")
        print(f"   Logo ID: {logo_id}")
        print(f"   Logo URL: {logo_url}")
        print(
            f"   You can use this URL in <img> tag: <img src='{logo_url}' alt='Logo'>")
    else:
        print(f"❌ Failed to upload logo: {response.text}")
        return

    # Step 4: Get all logos
    print("\n📋 Fetching all logos...")
    response = requests.get(f"{BASE_URL}/logos/", headers=headers)
    if response.status_code == 200:
        logos = response.json()["logos"]
        print(f"✅ Found {len(logos)} logo(s)")
        for logo in logos:
            print(
                f"   - ID: {logo['id']}, Filename: {logo['filename']}, URL: {logo['logo_url']}")
    else:
        print(f"❌ Failed to fetch logos: {response.text}")

    # Step 5: Get specific logo details
    print(f"\n🔍 Getting details for logo ID {logo_id}...")
    response = requests.get(f"{BASE_URL}/logos/{logo_id}", headers=headers)
    if response.status_code == 200:
        logo = response.json()["logo"]
        print("✅ Logo details:")
        print(f"   - ID: {logo['id']}")
        print(f"   - Filename: {logo['filename']}")
        print(f"   - URL: {logo['logo_url']}")
        print(f"   - File Size: {logo['file_size']} bytes")
        print(f"   - Content Type: {logo['content_type']}")
        print(f"   - Created: {logo['created_at']}")
    else:
        print(f"❌ Failed to get logo details: {response.text}")

    # Step 6: Delete the logo
    print(f"\n🗑️ Deleting logo ID {logo_id}...")
    response = requests.delete(f"{BASE_URL}/logos/{logo_id}", headers=headers)
    if response.status_code == 200:
        print("✅ Logo deleted successfully")
    else:
        print(f"❌ Failed to delete logo: {response.text}")

    # Verify deletion
    print("\n🔍 Verifying logo was deleted...")
    response = requests.get(f"{BASE_URL}/logos/", headers=headers)
    if response.status_code == 200:
        logos = response.json()["logos"]
        print(f"✅ Now showing {len(logos)} logo(s)")
    else:
        print(f"❌ Failed to verify deletion: {response.text}")


def test_authentication_required():
    """Test that authentication is required for logo endpoints"""
    print("\n🔒 Testing authentication requirements...")

    # Try to access without authentication
    response = requests.get(f"{BASE_URL}/logos/")
    if response.status_code == 401:
        print("✅ GET /logos/ correctly requires authentication")
    else:
        print(
            f"❌ GET /logos/ should require authentication but returned: {response.status_code}")

    # Try to upload without authentication
    files = {'logo': ('test.png', b'dummy', 'image/png')}
    response = requests.post(f"{BASE_URL}/logos/", files=files)
    if response.status_code == 401:
        print("✅ POST /logos/ correctly requires authentication")
    else:
        print(
            f"❌ POST /logos/ should require authentication but returned: {response.status_code}")


def test_file_validation():
    """Test file validation for logo uploads"""
    print("\n📁 Testing file validation...")

    # First login to get token
    login_data = {
        "email": "logotest@example.com",
        "password": "testpassword123"
    }

    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print("❌ Failed to login for file validation test")
        return

    token = response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test with invalid file type
    files = {'logo': ('test.txt', b'not an image', 'text/plain')}
    response = requests.post(f"{BASE_URL}/logos/",
                             files=files, headers=headers)
    if response.status_code == 400 and "Invalid file type" in response.text:
        print("✅ File type validation works correctly")
    else:
        print(
            f"❌ File type validation failed: {response.status_code} - {response.text}")

    # Test with no file
    response = requests.post(f"{BASE_URL}/logos/", headers=headers)
    if response.status_code == 400 and "No logo file provided" in response.text:
        print("✅ Missing file validation works correctly")
    else:
        print(
            f"❌ Missing file validation failed: {response.status_code} - {response.text}")


if __name__ == "__main__":
    print("🚀 Starting Logo API Tests...")
    print("="*50)

    try:
        test_authentication_required()
        test_file_validation()
        test_logo_api()

        print("\n" + "="*50)
        print("🎉 All tests completed!")
        print("\nTo use the logo URLs in HTML:")
        print("  <img src='https://your-bucket.s3.amazonaws.com/user123/logos/uuid-filename.png' alt='Logo'>")
        print("\nAPI Endpoints Summary:")
        print("  POST /logos/           - Upload a logo (requires auth)")
        print("  GET  /logos/           - Get all user logos (requires auth)")
        print("  GET  /logos/<id>       - Get specific logo details (requires auth)")
        print("  DELETE /logos/<id>     - Delete a logo (requires auth)")

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the Flask server.")
        print("   Make sure your Flask application is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
