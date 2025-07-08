"""
Customer Service API Controllers
FastAPI REST endpoints for customer operations
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from datetime import datetime
import logging

from ...application.services import CustomerApplicationService
from ...application.dto import (
    CreateCustomerRequest, UpdateCustomerRequest, CustomerResponse,
    CustomerListRequest, CustomerListResponse, UploadDocumentRequest,
    DocumentResponse, KYCUpdateRequest, CustomerStatsRequest, CustomerStatsResponse
)
from ...infrastructure.repositories import SQLAlchemyCustomerRepository, SQLAlchemyDocumentRepository
from ...infrastructure.database import init_database, health_check
from platform.shared.auth import verify_token, require_permissions

# Initialize FastAPI app
app = FastAPI(
    title="Customer Service API",
    description="Core Banking System - Customer Management Service",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security
security = HTTPBearer()

# Initialize repositories and services
customer_repository = SQLAlchemyCustomerRepository()
document_repository = SQLAlchemyDocumentRepository()
customer_service = CustomerApplicationService(
    customer_repository=customer_repository,
    document_repository=document_repository
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Dependency injection

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    try:
        token_data = verify_token(credentials.credentials)
        return token_data
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication token")


async def require_customer_read_permission(current_user = Depends(get_current_user)):
    """Require customer read permission"""
    if not require_permissions(current_user, ["customer:read"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user


async def require_customer_write_permission(current_user = Depends(get_current_user)):
    """Require customer write permission"""
    if not require_permissions(current_user, ["customer:write"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user


async def require_customer_admin_permission(current_user = Depends(get_current_user)):
    """Require customer admin permission"""
    if not require_permissions(current_user, ["customer:admin"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user


# Health check endpoints

@app.get("/health")
async def health_check_endpoint():
    """Health check endpoint"""
    try:
        db_healthy = health_check()
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "service": "customer-service",
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected" if db_healthy else "disconnected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "customer-service",
                "error": str(e)
            }
        )


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    try:
        # Check if service is ready to accept requests
        db_healthy = health_check()
        if not db_healthy:
            raise Exception("Database not available")
        
        return {
            "status": "ready",
            "service": "customer-service",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": "customer-service",
                "error": str(e)
            }
        )


# Customer management endpoints

@app.post("/customers", response_model=CustomerResponse)
async def create_customer(
    request: CreateCustomerRequest,
    current_user = Depends(require_customer_write_permission)
):
    """Create a new customer"""
    try:
        # Add audit info
        request.created_by = current_user["user_id"]
        
        response = await customer_service.create_customer(request)
        logger.info(f"Customer created: {response.customer_id} by {current_user['user_id']}")
        return response
        
    except ValueError as e:
        logger.warning(f"Customer creation validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Customer creation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    current_user = Depends(require_customer_read_permission)
):
    """Get customer by ID"""
    try:
        response = await customer_service.get_customer(customer_id)
        if not response:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        logger.info(f"Customer retrieved: {customer_id} by {current_user['user_id']}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get customer failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    request: UpdateCustomerRequest,
    current_user = Depends(require_customer_write_permission)
):
    """Update customer information"""
    try:
        # Add audit info
        request.updated_by = current_user["user_id"]
        
        response = await customer_service.update_customer(customer_id, request)
        logger.info(f"Customer updated: {customer_id} by {current_user['user_id']}")
        return response
        
    except ValueError as e:
        logger.warning(f"Customer update validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Customer update failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/customers", response_model=CustomerListResponse)
async def list_customers(
    customer_type: Optional[str] = None,
    status: Optional[str] = None,
    kyc_status: Optional[str] = None,
    risk_profile: Optional[str] = None,
    search_term: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user = Depends(require_customer_read_permission)
):
    """List customers with filters and pagination"""
    try:
        request = CustomerListRequest(
            customer_type=customer_type,
            status=status,
            kyc_status=kyc_status,
            risk_profile=risk_profile,
            search_term=search_term,
            page=page,
            size=size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        response = await customer_service.list_customers(request)
        logger.info(f"Customers listed by {current_user['user_id']}: page={page}, size={size}")
        return response
        
    except Exception as e:
        logger.error(f"List customers failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/customers/search")
async def search_customers(
    q: str,
    limit: int = 10,
    current_user = Depends(require_customer_read_permission)
):
    """Search customers by name, email, phone, or customer number"""
    try:
        results = await customer_service.search_customers(q, limit)
        logger.info(f"Customer search performed by {current_user['user_id']}: query='{q}'")
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Customer search failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: str,
    current_user = Depends(require_customer_admin_permission)
):
    """Delete customer (soft delete)"""
    try:
        success = await customer_service.delete_customer(customer_id)
        if not success:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        logger.info(f"Customer deleted: {customer_id} by {current_user['user_id']}")
        return {"message": "Customer deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete customer failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# KYC and compliance endpoints

@app.put("/customers/{customer_id}/kyc", response_model=CustomerResponse)
async def update_kyc_status(
    customer_id: str,
    request: KYCUpdateRequest,
    current_user = Depends(require_customer_write_permission)
):
    """Update customer KYC status"""
    try:
        # Add audit info
        request.updated_by = current_user["user_id"]
        
        response = await customer_service.update_kyc_status(customer_id, request)
        logger.info(f"KYC status updated: {customer_id} by {current_user['user_id']}")
        return response
        
    except ValueError as e:
        logger.warning(f"KYC update validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"KYC update failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/customers/{customer_id}/aml-screening")
async def perform_aml_screening(
    customer_id: str,
    current_user = Depends(require_customer_write_permission)
):
    """Perform AML screening for customer"""
    try:
        result = await customer_service.perform_aml_screening(customer_id)
        logger.info(f"AML screening performed: {customer_id} by {current_user['user_id']}")
        return result
        
    except ValueError as e:
        logger.warning(f"AML screening validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"AML screening failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/customers/{customer_id}/sanctions-screening")
async def perform_sanctions_screening(
    customer_id: str,
    current_user = Depends(require_customer_write_permission)
):
    """Perform sanctions screening for customer"""
    try:
        result = await customer_service.perform_sanctions_screening(customer_id)
        logger.info(f"Sanctions screening performed: {customer_id} by {current_user['user_id']}")
        return result
        
    except ValueError as e:
        logger.warning(f"Sanctions screening validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Sanctions screening failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Document management endpoints

@app.post("/customers/{customer_id}/documents", response_model=DocumentResponse)
async def upload_document(
    customer_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    document_name: str = Form(...),
    current_user = Depends(require_customer_write_permission)
):
    """Upload customer document"""
    try:
        # Read file content
        file_content = await file.read()
        
        request = UploadDocumentRequest(
            customer_id=customer_id,
            document_type=document_type,
            document_name=document_name,
            file_content=file_content,
            mime_type=file.content_type,
            uploaded_by=current_user["user_id"]
        )
        
        response = await customer_service.upload_document(request)
        logger.info(f"Document uploaded: {response.document_id} for customer {customer_id}")
        return response
        
    except ValueError as e:
        logger.warning(f"Document upload validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/customers/{customer_id}/documents", response_model=List[DocumentResponse])
async def get_customer_documents(
    customer_id: str,
    current_user = Depends(require_customer_read_permission)
):
    """Get all documents for a customer"""
    try:
        documents = await customer_service.get_customer_documents(customer_id)
        logger.info(f"Documents retrieved for customer: {customer_id}")
        return documents
        
    except Exception as e:
        logger.error(f"Get customer documents failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user = Depends(require_customer_read_permission)
):
    """Get document by ID"""
    try:
        document = await customer_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info(f"Document retrieved: {document_id}")
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.put("/documents/{document_id}/verify")
async def verify_document(
    document_id: str,
    verification_status: str = Form(...),
    verification_notes: str = Form(""),
    current_user = Depends(require_customer_write_permission)
):
    """Verify customer document"""
    try:
        result = await customer_service.verify_document(
            document_id, verification_status, verification_notes, current_user["user_id"]
        )
        logger.info(f"Document verified: {document_id} by {current_user['user_id']}")
        return result
        
    except ValueError as e:
        logger.warning(f"Document verification validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Document verification failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user = Depends(require_customer_admin_permission)
):
    """Delete customer document"""
    try:
        success = await customer_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info(f"Document deleted: {document_id} by {current_user['user_id']}")
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Statistics and reporting endpoints

@app.get("/customers/stats", response_model=CustomerStatsResponse)
async def get_customer_statistics(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    group_by: str = "month",
    current_user = Depends(require_customer_read_permission)
):
    """Get customer statistics"""
    try:
        request = CustomerStatsRequest(
            from_date=from_date or datetime.utcnow().replace(day=1),
            to_date=to_date or datetime.utcnow(),
            group_by=group_by
        )
        
        stats = await customer_service.get_customer_statistics(request)
        logger.info(f"Customer statistics retrieved by {current_user['user_id']}")
        return stats
        
    except Exception as e:
        logger.error(f"Get customer statistics failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Application startup and shutdown events

@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("Starting Customer Service...")
    try:
        # Initialize database
        init_database()
        logger.info("Customer Service started successfully")
    except Exception as e:
        logger.error(f"Failed to start Customer Service: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("Shutting down Customer Service...")


# Error handlers

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content={"error": "Validation Error", "detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
