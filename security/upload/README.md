# Upload Security

This directory contains components for secure file uploads with validation and scanning.

## Components

- `secure_upload.py` - Main secure file upload handler with validation
- `fixed_secure_upload.py` - Improved version of secure file upload handler

## Features

- MIME type validation
- File extension validation
- Content type vs extension matching
- File size limits
- Virus scanning integration (optional)
- Secure file storage
- Audit logging of upload events
- Flask integration

## Usage

```python
# Basic usage
from security.upload.secure_upload import SecureFileUpload

# Create an instance with custom upload directory
upload_handler = SecureFileUpload(upload_dir="/secure/uploads")

# Set allowed file types
upload_handler.set_allowed_extensions({'.pdf', '.jpg', '.png'})

# Handle an uploaded file
result = upload_handler.handle_upload(file)

# Check result
if result["success"]:
    print(f"File uploaded successfully to: {result['file_path']}")
else:
    print(f"Upload failed: {', '.join(result['errors'])}")

# Flask integration
from security.upload.secure_upload import handle_flask_upload
result = handle_flask_upload()
```

## Security Features

1. File type validation by extension and MIME type
2. Filename sanitization to prevent path traversal attacks
3. Content verification to prevent content/extension mismatch attacks
4. Size limits to prevent denial of service attacks
5. Optional virus scanning integration
6. Audit logging of all upload events
