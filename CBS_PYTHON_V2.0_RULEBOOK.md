# CBS_PYTHON V2.0 - Development Rulebook

## Directory Structure Rules

### Root Level Organization
```
CBS_PYTHON/
├── frontend/                    # Frontend Express.js application
├── backend/                     # Backend Flask/FastAPI application
├── documentation/               # Project documentation
├── archive/                     # Backup and legacy files
├── dump/                        # Legacy/deprecated files
└── README.md                    # Project overview
```

### Frontend Directory Structure
```
frontend/
├── server.js                    # Main Express server
├── package.json                 # Node.js dependencies
├── .env.example                 # Environment configuration template
├── public/                      # Static HTML files
│   ├── index.html
│   └── login.html
├── src/
│   ├── routes/                  # Express routes
│   │   ├── api.js              # API proxy routes
│   │   ├── auth.js             # Authentication routes
│   │   └── static.js           # Static file routes
│   ├── middleware/              # Express middleware
│   │   ├── auth.js             # Authentication middleware
│   │   ├── errorHandler.js     # Error handling middleware
│   │   └── logger.js           # Logging middleware
│   ├── assets/                  # Frontend assets
│   │   ├── css/                # Stylesheets
│   │   └── js/                 # JavaScript files
│   └── js/                      # JavaScript modules
│       └── banking-api-client.js # API client
└── logs/                        # Log files
```

### Backend Directory Structure
```
backend/
├── server.py                    # Main Flask/FastAPI server
├── requirements.txt             # Python dependencies
├── api/                         # API route definitions
├── controllers/                 # Request handlers
│   ├── auth_controller.py
│   ├── accounts_controller.py
│   ├── transactions_controller.py
│   └── customers_controller.py
├── services/                    # Business logic services
│   ├── account_service.py
│   ├── customer_service.py
│   ├── transaction_service.py
│   └── auth_service.py
├── middleware/                  # Flask middleware
├── encryption/                  # Encryption services
├── models/                      # Database models
├── database/                    # Database connections and migrations
├── utils/                       # Utility functions
└── tests/                       # Backend tests
```

### Core Banking Module Structure
```
core_banking/
├── accounts/                    # Account management
├── customer_management/         # Customer operations
├── transactions/               # Transaction processing
├── loans/                      # Loan management
├── database/                   # Database connections
└── utils/                      # Shared utilities
```

## Code Organization Rules

### File Naming Conventions
- **Python files**: `snake_case.py`
- **JavaScript files**: `camelCase.js` or `kebab-case.js`
- **CSS files**: `kebab-case.css`
- **HTML files**: `kebab-case.html`
- **Configuration files**: `UPPERCASE.ext` or `lowercase.ext`

### Module Organization
- **One class per file** for major components
- **Related functions grouped** in utility modules
- **Constants defined** at module level
- **Import statements** at the top of files
- **Export statements** at the bottom of files

### Code Structure Rules
```python
# Python file structure
"""
Module docstring describing purpose and usage
"""

# Standard library imports
import os
import sys

# Third-party imports
from flask import Flask, request

# Local imports
from .utils import helper_function
from .models import DatabaseModel

# Constants
CONSTANT_VALUE = "value"

# Classes
class ServiceClass:
    """Class docstring"""
    
    def __init__(self):
        """Initialize the service"""
        pass
    
    def public_method(self):
        """Public method docstring"""
        pass
    
    def _private_method(self):
        """Private method docstring"""
        pass

# Functions
def public_function():
    """Function docstring"""
    pass

# Main execution
if __name__ == "__main__":
    main()
```

## Coding Standards

### Python Code Standards
- **PEP 8 compliance**: Follow Python style guide
- **Type hints**: Use type annotations for functions
- **Docstrings**: Use Google or NumPy style docstrings
- **Error handling**: Comprehensive try-catch blocks
- **Logging**: Use structured logging with appropriate levels

### JavaScript Code Standards
- **ES6+ features**: Use modern JavaScript features
- **Consistent formatting**: Use Prettier or similar formatter
- **JSDoc comments**: Document functions and classes
- **Error handling**: Use try-catch and proper error propagation
- **Async/await**: Prefer async/await over promises

### Database Standards
- **Naming conventions**: Use snake_case for tables and columns
- **Indexing**: Proper indexing for performance
- **Constraints**: Use database constraints for data integrity
- **Migrations**: Version-controlled database migrations
- **Transactions**: Use transactions for data consistency

## Security Rules

### Data Protection
- **Encryption**: All sensitive data must be encrypted
- **Input validation**: Validate all user inputs
- **Output encoding**: Encode all outputs to prevent XSS
- **SQL injection prevention**: Use parameterized queries
- **Authentication**: Implement strong authentication mechanisms

### API Security
- **Authentication**: All API endpoints require authentication
- **Authorization**: Implement role-based access control
- **Rate limiting**: Implement request rate limiting
- **HTTPS**: Use HTTPS for all communications
- **CORS**: Configure CORS properly

### Code Security
- **Secrets management**: No hardcoded secrets
- **Environment variables**: Use environment variables for configuration
- **Dependency scanning**: Regular dependency vulnerability scanning
- **Code review**: Mandatory security code reviews
- **Audit logging**: Log all security-relevant events

## Testing Standards

### Test Organization
```
tests/
├── unit/                        # Unit tests
│   ├── backend/
│   │   ├── test_auth_controller.py
│   │   ├── test_accounts_controller.py
│   │   └── test_transactions_controller.py
│   └── frontend/
│       └── test_api_client.js
├── integration/                 # Integration tests
│   ├── test_api_integration.py
│   └── test_database_integration.py
├── end_to_end/                  # E2E tests
│   ├── test_user_journeys.py
│   └── test_banking_workflows.py
├── performance/                 # Performance tests
│   ├── test_load_performance.py
│   └── test_stress_testing.py
└── security/                    # Security tests
    ├── test_authentication.py
    └── test_authorization.py
```

### Test Writing Rules
- **Test naming**: Use descriptive test names
- **Test isolation**: Each test should be independent
- **Test data**: Use fixtures for test data
- **Assertions**: Use meaningful assertions
- **Coverage**: Minimum 85% code coverage

### Test Types
- **Unit tests**: Test individual functions/methods
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete user workflows
- **Performance tests**: Test system performance
- **Security tests**: Test security controls

## Error Handling Rules

### Error Response Format
```json
{
  "error": true,
  "message": "User-friendly error message",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req-12345",
  "details": {
    "field": "validation error details"
  }
}
```

### Error Logging
- **Structured logging**: Use JSON format for logs
- **Log levels**: Use appropriate log levels (ERROR, WARN, INFO, DEBUG)
- **Context information**: Include request ID and user context
- **Sensitive data**: Never log sensitive information
- **Error tracking**: Use error tracking systems

## Performance Rules

### Frontend Performance
- **Bundle size**: Minimize JavaScript bundle size
- **Lazy loading**: Implement lazy loading for resources
- **Caching**: Implement proper caching strategies
- **Compression**: Use gzip compression
- **CDN**: Use CDN for static assets

### Backend Performance
- **Database queries**: Optimize database queries
- **Connection pooling**: Use database connection pooling
- **Caching**: Implement Redis caching
- **Async processing**: Use async processing for heavy tasks
- **Load balancing**: Implement load balancing

### API Performance
- **Response time**: API responses < 200ms
- **Pagination**: Implement pagination for large datasets
- **Rate limiting**: Implement rate limiting
- **Monitoring**: Monitor API performance metrics
- **Optimization**: Regular performance optimization

## Documentation Rules

### Code Documentation
- **Inline comments**: Explain complex logic
- **Function documentation**: Document all public functions
- **Class documentation**: Document all public classes
- **Module documentation**: Document module purpose
- **README files**: Include README in each module

### API Documentation
- **OpenAPI specification**: Use OpenAPI for API documentation
- **Request/response examples**: Include examples
- **Error responses**: Document error responses
- **Authentication**: Document authentication requirements
- **Rate limits**: Document rate limiting rules

### User Documentation
- **User guides**: Create user guides for features
- **Installation guides**: Document installation procedures
- **Configuration guides**: Document configuration options
- **Troubleshooting**: Include troubleshooting guides
- **FAQ**: Maintain frequently asked questions

## Deployment Rules

### Environment Configuration
- **Environment separation**: Separate dev, test, and prod environments
- **Configuration management**: Use configuration management tools
- **Secrets management**: Use secure secrets management
- **Environment variables**: Use environment variables for configuration
- **Version control**: Version control all configuration

### Deployment Process
- **Automated deployment**: Use CI/CD pipelines
- **Testing**: Run all tests before deployment
- **Rollback plan**: Have rollback procedures
- **Monitoring**: Monitor deployment success
- **Documentation**: Document deployment procedures

### Infrastructure as Code
- **Version control**: Version control infrastructure code
- **Reproducibility**: Ensure reproducible deployments
- **Documentation**: Document infrastructure setup
- **Backup procedures**: Implement backup procedures
- **Disaster recovery**: Plan disaster recovery procedures

## Monitoring Rules

### Application Monitoring
- **Health checks**: Implement health check endpoints
- **Metrics collection**: Collect application metrics
- **Alert configuration**: Configure monitoring alerts
- **Dashboard creation**: Create monitoring dashboards
- **Log aggregation**: Aggregate application logs

### Performance Monitoring
- **Response time monitoring**: Monitor API response times
- **Error rate monitoring**: Monitor error rates
- **Resource utilization**: Monitor system resources
- **Database performance**: Monitor database performance
- **User experience**: Monitor user experience metrics

## Code Review Rules

### Review Process
- **Mandatory reviews**: All code must be reviewed
- **Review checklist**: Use code review checklist
- **Security review**: Include security review
- **Performance review**: Consider performance impact
- **Documentation review**: Review documentation updates

### Review Criteria
- **Code quality**: Check code quality and standards
- **Functionality**: Verify functionality works correctly
- **Security**: Check for security vulnerabilities
- **Performance**: Consider performance implications
- **Maintainability**: Assess code maintainability

## Version Control Rules

### Git Workflow
- **Branch naming**: Use descriptive branch names
- **Commit messages**: Write clear commit messages
- **Pull requests**: Use pull requests for code changes
- **Code review**: Mandatory code review before merge
- **Release tagging**: Tag releases appropriately

### Branching Strategy
- **Main branch**: Protected main branch
- **Development branch**: Active development branch
- **Feature branches**: Create feature branches
- **Release branches**: Create release branches
- **Hotfix branches**: Create hotfix branches

## Maintenance Rules

### Regular Maintenance
- **Dependency updates**: Regular dependency updates
- **Security patches**: Apply security patches promptly
- **Performance optimization**: Regular performance reviews
- **Code refactoring**: Regular code refactoring
- **Documentation updates**: Keep documentation current

### Backup Procedures
- **Database backups**: Regular database backups
- **Code backups**: Code repository backups
- **Configuration backups**: Configuration backups
- **Recovery testing**: Test recovery procedures
- **Disaster recovery**: Maintain disaster recovery plan

---

**Rulebook Version**: 1.0  
**Last Updated**: January 2024  
**Next Review**: Quarterly
