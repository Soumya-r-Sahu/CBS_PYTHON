# Core Banking System V3.0 - Backend Implementation

## Overview

This is the backend implementation of the Core Banking System V3.0, built using a modern microservices architecture with FastAPI, PostgreSQL, and JWT authentication.

## Architecture

### Microservices Structure

```
backend/
├── api_gateway/              # API Gateway - Routes requests to services
│   ├── gateway.py           # Main gateway application
│   └── ...
├── services/                 # Individual microservices
│   ├── auth_service/        # Authentication & Authorization
│   ├── customer_service/    # Customer Management
│   ├── account_service/     # Account Operations
│   ├── transaction_service/ # Transaction Processing
│   ├── payment_service/     # Payment Processing
│   ├── loan_service/        # Loan Management
│   ├── notification_service/# Notifications
│   └── reporting_service/   # Reports & Analytics
├── shared/                  # Shared utilities and models
│   ├── database/           # Database connection & management
│   ├── models/             # SQLAlchemy models
│   ├── utils/              # Utility functions
│   └── security/           # Security utilities
└── start_services.sh       # Service startup script
```

### Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with passlib
- **API Documentation**: Automatic OpenAPI/Swagger
- **Inter-service Communication**: HTTP with httpx
- **Validation**: Pydantic models
- **Environment**: Python 3.8+

## Services

### 1. Authentication Service (Port 8001)
- User login/logout
- JWT token management
- User creation and management
- Role-based access control

**Endpoints:**
- `POST /login` - User login
- `POST /refresh` - Refresh token
- `POST /logout` - User logout
- `GET /me` - Get current user info
- `POST /users` - Create new user (Admin only)

### 2. Customer Service (Port 8003)
- Customer registration and management
- Customer profile updates
- Customer search and listing
- Customer status management

**Endpoints:**
- `POST /customers` - Create customer
- `GET /customers/{customer_id}` - Get customer details
- `PUT /customers/{customer_id}` - Update customer
- `GET /customers` - Search customers
- `GET /customers/{customer_id}/accounts` - Get customer accounts
- `PATCH /customers/{customer_id}/status` - Update status

### 3. Account Service (Port 8002)
- Account creation and management
- Balance operations (deposit/withdrawal)
- Account transactions
- Account status management

**Endpoints:**
- `POST /accounts` - Create account
- `GET /accounts/{account_number}` - Get account details
- `GET /accounts/{account_number}/balance` - Get balance
- `POST /accounts/{account_number}/deposit` - Deposit money
- `POST /accounts/{account_number}/withdraw` - Withdraw money
- `GET /accounts/{account_number}/transactions` - Get transactions

### 4. API Gateway (Port 8000)
- Routes requests to appropriate services
- Handles CORS and security headers
- Provides unified API interface
- Health monitoring

**Endpoints:**
- All service endpoints are accessible through `/api/{service}/...`
- `GET /health` - Overall system health

## Database Models

### Core Models

1. **User** - System users (employees, customers)
2. **Customer** - Bank customers
3. **Account** - Bank accounts (savings, current, etc.)
4. **Transaction** - All financial transactions
5. **Branch** - Bank branches

### Model Features

- **Base Model**: Common fields (id, uuid, created_at, updated_at, is_active)
- **Enums**: Strong typing for status fields
- **Relationships**: Proper foreign key relationships
- **Validation**: Built-in validation methods
- **UUID**: Unique identifiers for external references

## Security Features

### Authentication
- JWT-based authentication
- Secure password hashing with bcrypt
- Token refresh mechanism
- Role-based access control

### Authorization
- Employee-only operations
- Admin-only functions
- Customer-specific access controls
- Service-level permissions

### Data Protection
- Password hashing
- Sensitive data handling
- Input validation
- SQL injection prevention

## Setup and Installation

### Prerequisites

1. Python 3.8+
2. PostgreSQL 12+
3. pip or conda

### Installation Steps

1. **Install Dependencies**
   ```bash
   cd /home/asus/CBS_PYTHON/backend
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   # Create PostgreSQL database
   createdb core_banking
   
   # Set environment variables
   export DB_USER=postgres
   export DB_PASSWORD=your_password
   export DB_HOST=localhost
   export DB_PORT=5432
   export DB_NAME=core_banking
   export JWT_SECRET_KEY=your-secret-key
   ```

3. **Start Services**
   ```bash
   # Start all services
   ./start_services.sh
   
   # Or start individual services
   cd services/auth_service
   uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```

### Environment Variables

Required environment variables:

```bash
# Database Configuration
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=core_banking
DB_ECHO=false

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production

# Service URLs (optional, defaults provided)
AUTH_SERVICE_URL=http://localhost:8001
CUSTOMER_SERVICE_URL=http://localhost:8003
ACCOUNT_SERVICE_URL=http://localhost:8002
```

## API Usage

### Authentication Flow

1. **Login**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "password"}'
   ```

2. **Use Token**
   ```bash
   curl -X GET http://localhost:8000/api/customers \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

### Customer Management

1. **Create Customer**
   ```bash
   curl -X POST http://localhost:8000/api/customers \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "first_name": "John",
       "last_name": "Doe",
       "date_of_birth": "1990-01-01",
       "gender": "MALE",
       "email": "john.doe@example.com",
       "phone": "1234567890",
       "address_line1": "123 Main St",
       "city": "Mumbai",
       "state": "Maharashtra",
       "postal_code": "400001"
     }'
   ```

### Account Operations

1. **Create Account**
   ```bash
   curl -X POST http://localhost:8000/api/accounts \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "customer_id": 1,
       "account_type": "SAVINGS",
       "initial_deposit": 1000.00,
       "branch_code": "BR001",
       "ifsc_code": "BANK0000001"
     }'
   ```

2. **Deposit Money**
   ```bash
   curl -X POST http://localhost:8000/api/accounts/AC-20250709-123456/deposit \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "amount": 500.00,
       "description": "Cash deposit"
     }'
   ```

## Development

### Adding New Services

1. Create service directory in `services/`
2. Implement FastAPI application with health endpoint
3. Add database models if needed
4. Update API Gateway routing
5. Add service URL to startup script

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migration
alembic upgrade head
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

## API Documentation

Each service provides interactive API documentation:

- **Auth Service**: http://localhost:8001/docs
- **Customer Service**: http://localhost:8003/docs
- **Account Service**: http://localhost:8002/docs
- **API Gateway**: http://localhost:8000/docs

## Monitoring and Health

### Health Checks

- **Overall Health**: http://localhost:8000/health
- **Individual Services**: http://localhost:800X/health

### Logs

Services log to stdout/stderr. In production, configure proper log aggregation.

## Production Deployment

### Docker Deployment

1. Create Dockerfiles for each service
2. Use Docker Compose for orchestration
3. Configure environment variables
4. Set up reverse proxy (nginx)
5. Enable HTTPS/TLS

### Kubernetes Deployment

1. Create Kubernetes manifests
2. Configure ConfigMaps and Secrets
3. Set up Ingress controllers
4. Configure horizontal pod autoscaling
5. Set up monitoring and logging

### Security Considerations

1. Change default JWT secret key
2. Use secure database passwords
3. Enable database SSL/TLS
4. Configure proper CORS origins
5. Implement rate limiting
6. Set up API security scanning
7. Enable audit logging

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port
   lsof -i :8000
   
   # Kill process
   kill -9 PID
   ```

2. **Database Connection Error**
   - Check PostgreSQL is running
   - Verify connection parameters
   - Check database exists

3. **Import Errors**
   - Ensure all dependencies installed
   - Check Python path
   - Verify virtual environment

4. **Authentication Issues**
   - Check JWT secret key
   - Verify token format
   - Check user permissions

## Support

For issues and questions:

1. Check logs for error details
2. Verify environment configuration
3. Test individual service health endpoints
4. Check database connectivity
5. Review API documentation

## License

This project is part of the Core Banking System V3.0 and is proprietary software.
