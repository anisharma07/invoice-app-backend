import re
from urllib.parse import urlparse


def validate_input(data, required_fields):
    missing = [field for field in required_fields if field not in data]
    if missing:
        return False, f"Missing fields: {', '.join(missing)}"
    return True, None


def validate_url(url):
    """Validate if a URL is properly formatted and uses allowed schemes"""
    try:
        # Basic URL structure validation
        parsed = urlparse(url)

        # Check if scheme and netloc are present
        if not parsed.scheme or not parsed.netloc:
            return False

        # Allow only http and https schemes
        if parsed.scheme not in ['http', 'https']:
            return False

        # Basic domain validation using regex
        domain_pattern = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        )

        if not domain_pattern.match(parsed.netloc.split(':')[0]):
            return False

        return True

    except Exception:
        return False


def validate_email(email):
    """Validate email format"""
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(email_pattern.match(email))


def validate_file_extension(filename, allowed_extensions):
    """Validate if file has an allowed extension"""
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
