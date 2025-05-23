# Django UI Integration Guide 🖥️

This guide provides instructions for integrating Django's frontend with the CBS_PYTHON system.

## Steps 📋

1. **Setup Django Templates**: Configure template directories.
2. **Integrate Static Files**: Link CSS and JavaScript.
3. **Test Frontend Components**: Ensure compatibility with CBS_PYTHON APIs.

_Last updated: May 23, 2025_

## Setup for Testing

1. Install required Python packages:
```bash
pip install requests django djangorestframework djangorestframework-simplejwt
```

2. Run tests specifically for Django:
```bash
python -m Tests.integration.comprehensive_framework_tests DjangoCompatibilityTest
```

## Test Coverage

The Django compatibility tests verify:

- Authentication using the Django client
- CSRF token handling
- Account operations (create, read, update, delete)
- Transaction operations
- Card operations
- Profile management
- UPI operations

## Common Django Integration Issues

### CSRF Token Handling

Django's CSRF protection requires special handling for forms and AJAX requests. The Django client library automatically handles this by:

1. Extracting the CSRF token from cookies
2. Adding it to request headers
3. Managing token refreshing

### Session Management

Django uses session-based authentication by default, while the API uses JWT tokens. Our integration:

1. Stores JWT tokens in the Django session
2. Automatically adds them to API requests
3. Handles token expiration and renewal

### Template Integration

The Django templates in the demo frontend show how to:

1. Display API data in Django templates
2. Handle loading states
3. Implement form submission with API validation
4. Manage error handling and user feedback

### Django ORM vs. API Calls

The demo shows how to work with Django views that use API calls rather than the Django ORM, demonstrating:

1. How to map API responses to template contexts
2. Pagination handling
3. Error handling and user feedback
4. Form validation against API responses
