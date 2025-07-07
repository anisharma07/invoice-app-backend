from flask import Blueprint, request, jsonify
import jwt
import uuid
import os
from services.database import cursor, conn
from services.s3 import s3_client, BUCKET_NAME
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get secret key from environment variable
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "your-secret-key-here-change-this-in-production")

logo_bp = Blueprint('logo', __name__)


def get_user_from_token(token):
    """Extract user ID from JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload.get('user_id')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def validate_image_file(file):
    """Validate if uploaded file is an image"""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    allowed_mime_types = {
        'image/png', 'image/jpeg', 'image/jpg', 'image/gif',
        'image/webp', 'image/svg+xml'
    }

    if file and file.filename:
        filename_ext = file.filename.rsplit(
            '.', 1)[1].lower() if '.' in file.filename else ''
        return (filename_ext in allowed_extensions and
                file.content_type in allowed_mime_types)
    return False


@logo_bp.route('/', methods=['POST'])
def upload_logo():
    """Upload a logo for authenticated user"""
    try:
        # Check authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authentication required"}), 401

        token = auth_header.split(' ')[1]
        user_id = get_user_from_token(token)

        if not user_id:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Check if file is provided
        if 'logo' not in request.files:
            return jsonify({"error": "No logo file provided"}), 400

        file = request.files['logo']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Validate file is an image
        if not validate_image_file(file):
            return jsonify({"error": "Invalid file type. Only images are allowed (PNG, JPG, JPEG, GIF, WebP, SVG)"}), 400

        # Check file size (max 5MB)
        file.seek(0, 2)  # Seek to end of file
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        if file_size > 5 * 1024 * 1024:  # 5MB limit
            return jsonify({"error": "File size too large. Maximum 5MB allowed"}), 400

        # Prepare file data
        file_name = file.filename
        file_content = file.read()
        content_type = file.content_type

        # Generate unique filename and S3 key (logos/user<id>/ structure)
        unique_filename = f"{uuid.uuid4()}-{file_name}"
        s3_key = f"logos/user{user_id}/{unique_filename}"

        # Upload to S3 (no ACL since bucket owner enforced is set)
        print(f"Uploading to S3: Bucket={BUCKET_NAME}, Key={s3_key}")
        try:
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type
            )
            print(f"✅ Successfully uploaded to S3: {s3_key}")
        except Exception as s3_error:
            print(f"❌ S3 upload error: {s3_error}")
            raise s3_error

        # Generate public URL (works because bucket policy allows public read for logos/*)
        logo_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_key}"

        # Save logo metadata to database
        cursor.execute(
            "INSERT INTO user_logos (user_id, filename, s3_key, logo_url, file_size, content_type, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (user_id, file_name, s3_key, logo_url,
             file_size, content_type, datetime.now())
        )
        result = cursor.fetchone()

        if result:
            conn.commit()
            return jsonify({
                "success": True,
                "logo_id": result['id'],
                "filename": file_name,
                "logo_url": logo_url,
                "file_size": file_size,
                "message": "Logo uploaded successfully"
            }), 201
        else:
            return jsonify({"error": "Failed to save logo metadata"}), 500

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500


@logo_bp.route('/', methods=['GET'])
def get_logos():
    """Get all logos for authenticated user"""
    try:
        # Check authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authentication required"}), 401

        token = auth_header.split(' ')[1]
        user_id = get_user_from_token(token)

        if not user_id:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Get user's logos from database
        cursor.execute(
            """SELECT id, filename, s3_key, logo_url, file_size, content_type, created_at 
               FROM user_logos 
               WHERE user_id = %s 
               ORDER BY created_at DESC""",
            (user_id,)
        )
        logos = cursor.fetchall()

        return jsonify({
            "success": True,
            "logos": [dict(logo) for logo in logos]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@logo_bp.route('/<int:logo_id>', methods=['DELETE'])
def delete_logo(logo_id):
    """Delete a specific logo for authenticated user"""
    try:
        # Check authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authentication required"}), 401

        token = auth_header.split(' ')[1]
        user_id = get_user_from_token(token)

        if not user_id:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Check if logo exists and belongs to user
        cursor.execute(
            "SELECT s3_key FROM user_logos WHERE id = %s AND user_id = %s",
            (logo_id, user_id)
        )
        logo = cursor.fetchone()

        if not logo:
            return jsonify({"error": "Logo not found or access denied"}), 404

        # Delete from S3
        try:
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=logo['s3_key'])
        except Exception as s3_error:
            print(f"Error deleting from S3: {s3_error}")
            # Continue with database deletion even if S3 deletion fails

        # Delete from database
        cursor.execute(
            "DELETE FROM user_logos WHERE id = %s AND user_id = %s",
            (logo_id, user_id)
        )

        if cursor.rowcount > 0:
            conn.commit()
            return jsonify({
                "success": True,
                "message": "Logo deleted successfully"
            })
        else:
            return jsonify({"error": "Failed to delete logo"}), 500

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500


@logo_bp.route('/<int:logo_id>', methods=['GET'])
def get_logo_details(logo_id):
    """Get details of a specific logo for authenticated user"""
    try:
        # Check authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authentication required"}), 401

        token = auth_header.split(' ')[1]
        user_id = get_user_from_token(token)

        if not user_id:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Get logo details
        cursor.execute(
            """SELECT id, filename, s3_key, logo_url, file_size, content_type, created_at 
               FROM user_logos 
               WHERE id = %s AND user_id = %s""",
            (logo_id, user_id)
        )
        logo = cursor.fetchone()

        if logo:
            return jsonify({
                "success": True,
                "logo": dict(logo)
            })
        else:
            return jsonify({"error": "Logo not found or access denied"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@logo_bp.route('/test-upload', methods=['POST'])
def test_upload():
    """Test endpoint to debug S3 upload issues"""
    try:
        # Check authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authentication required"}), 401

        token = auth_header.split(' ')[1]
        user_id = get_user_from_token(token)

        if not user_id:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Create a simple test file
        test_content = b"test logo content"
        test_key = f"logos/user{user_id}/test-logo.txt"

        print(f"Testing S3 upload: Bucket={BUCKET_NAME}, Key={test_key}")

        try:
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=test_key,
                Body=test_content,
                ContentType='text/plain'
            )

            # Clean up test file
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=test_key)

            return jsonify({
                "success": True,
                "message": "S3 upload test successful",
                "bucket": BUCKET_NAME,
                "test_key": test_key
            })

        except Exception as s3_error:
            return jsonify({
                "success": False,
                "error": f"S3 error: {str(s3_error)}",
                "bucket": BUCKET_NAME,
                "test_key": test_key
            }), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
