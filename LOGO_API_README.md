# Logo API Documentation

## Overview

The Logo API allows authenticated users to upload, manage, and delete logo images stored in AWS S3. All logo files are stored in the `/user<id>/logos/` folder structure in your S3 bucket.

## Database Schema

The `user_logos` table stores logo metadata:

```sql
CREATE TABLE user_logos (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    s3_key TEXT NOT NULL,
    logo_url TEXT NOT NULL,
    file_size INTEGER,
    content_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Authentication

All logo endpoints require JWT authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## API Endpoints

### 1. Upload Logo

**POST** `/logos/`

Upload a new logo image for the authenticated user.

**Headers:**

- `Authorization: Bearer <jwt_token>`
- `Content-Type: multipart/form-data`

**Form Data:**

- `logo`: Image file (PNG, JPG, JPEG, GIF, WebP, SVG)

**File Restrictions:**

- Maximum file size: 5MB
- Allowed formats: PNG, JPG, JPEG, GIF, WebP, SVG
- Only image MIME types accepted

**Success Response (201):**

```json
{
    "success": true,
    "logo_id": 1,
    "filename": "company-logo.png",
    "logo_url": "https://your-bucket.s3.amazonaws.com/user123/logos/uuid-company-logo.png",
    "file_size": 15432,
    "message": "Logo uploaded successfully"
}
```

**Error Responses:**

- `400`: Invalid file type, no file provided, or file too large
- `401`: Authentication required or invalid token
- `500`: Server error

### 2. Get All Logos

**GET** `/logos/`

Retrieve all logos for the authenticated user.

**Headers:**

- `Authorization: Bearer <jwt_token>`

**Success Response (200):**

```json
{
    "success": true,
    "logos": [
        {
            "id": 1,
            "filename": "company-logo.png",
            "s3_key": "user123/logos/uuid-company-logo.png",
            "logo_url": "https://your-bucket.s3.amazonaws.com/user123/logos/uuid-company-logo.png",
            "file_size": 15432,
            "content_type": "image/png",
            "created_at": "2025-01-07T10:30:00"
        }
    ]
}
```

### 3. Get Logo Details

**GET** `/logos/<logo_id>`

Get details of a specific logo.

**Headers:**

- `Authorization: Bearer <jwt_token>`

**URL Parameters:**

- `logo_id`: Integer ID of the logo

**Success Response (200):**

```json
{
    "success": true,
    "logo": {
        "id": 1,
        "filename": "company-logo.png",
        "s3_key": "user123/logos/uuid-company-logo.png",
        "logo_url": "https://your-bucket.s3.amazonaws.com/user123/logos/uuid-company-logo.png",
        "file_size": 15432,
        "content_type": "image/png",
        "created_at": "2025-01-07T10:30:00"
    }
}
```

**Error Responses:**

- `401`: Authentication required or invalid token
- `404`: Logo not found or access denied

### 4. Delete Logo

**DELETE** `/logos/<logo_id>`

Delete a specific logo from both S3 and database.

**Headers:**

- `Authorization: Bearer <jwt_token>`

**URL Parameters:**

- `logo_id`: Integer ID of the logo to delete

**Success Response (200):**

```json
{
    "success": true,
    "message": "Logo deleted successfully"
}
```

**Error Responses:**

- `401`: Authentication required or invalid token
- `404`: Logo not found or access denied
- `500`: Server error

## Usage in HTML

Once uploaded, you can use the logo URL directly in HTML:

```html
<img src="https://your-bucket.s3.amazonaws.com/user123/logos/uuid-company-logo.png"
     alt="Company Logo"
     style="max-width: 200px; height: auto;">
```

## S3 Configuration

Make sure your S3 bucket has the following configuration:

### 1. Bucket Policy (for public read access to logos)

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::your-bucket-name/user*/logos/*"
        }
    ]
}
```

### 2. CORS Configuration

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": []
    }
]
```

## Example Usage with cURL

### Upload a logo:

```bash
curl -X POST http://localhost:5000/logos/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "logo=@/path/to/your/logo.png"
```

### Get all logos:

```bash
curl -X GET http://localhost:5000/logos/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Delete a logo:

```bash
curl -X DELETE http://localhost:5000/logos/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## File Storage Structure

Logos are stored in S3 with the following structure:

```
your-s3-bucket/
├── user1/
│   └── logos/
│       ├── uuid1-logo1.png
│       └── uuid2-logo2.jpg
├── user2/
│   └── logos/
│       └── uuid3-logo3.png
└── ...
```

## Security Features

- **Authentication Required**: All endpoints require valid JWT tokens
- **File Type Validation**: Only image files are accepted
- **File Size Limits**: Maximum 5MB per file
- **User Isolation**: Users can only access their own logos
- **Unique Filenames**: UUIDs prevent filename conflicts
- **Public URLs**: Logos are publicly accessible via direct S3 URLs
