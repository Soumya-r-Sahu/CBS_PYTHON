"""
API Gateway for Core Banking System V3.0

This gateway routes requests to appropriate microservices and handles cross-cutting concerns.
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from typing import Optional

from ..shared.database import init_database, check_database_health

app = FastAPI(
    title="Core Banking API Gateway",
    description="API Gateway for Core Banking System V3.0",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
SERVICE_URLS = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://localhost:8001"),
    "customer": os.getenv("CUSTOMER_SERVICE_URL", "http://localhost:8003"),
    "account": os.getenv("ACCOUNT_SERVICE_URL", "http://localhost:8002"),
    "transaction": os.getenv("TRANSACTION_SERVICE_URL", "http://localhost:8004"),
    "payment": os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8005"),
    "loan": os.getenv("LOAN_SERVICE_URL", "http://localhost:8006"),
    "notification": os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8007"),
    "reporting": os.getenv("REPORTING_SERVICE_URL", "http://localhost:8008"),
}

# HTTP Client for service communication
client = httpx.AsyncClient(timeout=30.0)

async def proxy_request(service_name: str, path: str, method: str, headers: dict, body: bytes = None):
    """Proxy request to microservice"""
    service_url = SERVICE_URLS.get(service_name)
    if not service_url:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    url = f"{service_url}{path}"
    
    try:
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            content=body
        )
        return response
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header"""
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    """Gateway health check"""
    services_health = {}
    
    # Check database
    services_health["database"] = check_database_health()
    
    # Check each service
    for service_name, service_url in SERVICE_URLS.items():
        try:
            response = await client.get(f"{service_url}/health", timeout=5.0)
            services_health[service_name] = response.status_code == 200
        except:
            services_health[service_name] = False
    
    all_healthy = all(services_health.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": services_health,
        "version": "3.0.0"
    }

# Authentication routes
@app.post("/api/auth/login")
async def login(request: Request):
    """User login"""
    body = await request.body()
    response = await proxy_request("auth", "/login", "POST", dict(request.headers), body)
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.post("/api/auth/refresh")
async def refresh_token(request: Request):
    """Refresh access token"""
    body = await request.body()
    response = await proxy_request("auth", "/refresh", "POST", dict(request.headers), body)
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.post("/api/auth/logout")
async def logout(request: Request):
    """User logout"""
    response = await proxy_request("auth", "/logout", "POST", dict(request.headers))
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/api/auth/me")
async def get_current_user(request: Request):
    """Get current user info"""
    response = await proxy_request("auth", "/me", "GET", dict(request.headers))
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.post("/api/auth/users")
async def create_user(request: Request):
    """Create new user"""
    body = await request.body()
    response = await proxy_request("auth", "/users", "POST", dict(request.headers), body)
    return JSONResponse(content=response.json(), status_code=response.status_code)

# Customer routes
@app.post("/api/customers")
async def create_customer(request: Request):
    """Create new customer"""
    body = await request.body()
    response = await proxy_request("customer", "/customers", "POST", dict(request.headers), body)
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/api/customers/{customer_id}")
async def get_customer(customer_id: str, request: Request):
    """Get customer by ID"""
    response = await proxy_request("customer", f"/customers/{customer_id}", "GET", dict(request.headers))
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.put("/api/customers/{customer_id}")
async def update_customer(customer_id: str, request: Request):
    """Update customer"""
    body = await request.body()
    response = await proxy_request("customer", f"/customers/{customer_id}", "PUT", dict(request.headers), body)
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/api/customers")
async def search_customers(request: Request):
    """Search customers"""
    response = await proxy_request("customer", f"/customers?{request.url.query}", "GET", dict(request.headers))
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/api/customers/{customer_id}/accounts")
async def get_customer_accounts(customer_id: str, request: Request):
    """Get customer accounts"""
    response = await proxy_request("customer", f"/customers/{customer_id}/accounts", "GET", dict(request.headers))
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.patch("/api/customers/{customer_id}/status")
async def update_customer_status(customer_id: str, request: Request):
    """Update customer status"""
    body = await request.body()
    response = await proxy_request("customer", f"/customers/{customer_id}/status", "PATCH", dict(request.headers), body)
    return JSONResponse(content=response.json(), status_code=response.status_code)

# Account routes
@app.post("/api/accounts")
async def create_account(request: Request):
    """Create new account"""
    body = await request.body()
    response = await proxy_request("account", "/accounts", "POST", dict(request.headers), body)
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/api/accounts/{account_number}")
async def get_account(account_number: str, request: Request):
    """Get account details"""
    response = await proxy_request("account", f"/accounts/{account_number}", "GET", dict(request.headers))
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/api/accounts/{account_number}/balance")
async def get_account_balance(account_number: str, request: Request):
    """Get account balance"""
    response = await proxy_request("account", f"/accounts/{account_number}/balance", "GET", dict(request.headers))
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.post("/api/accounts/{account_number}/deposit")
async def deposit_money(account_number: str, request: Request):
    """Deposit money"""
    body = await request.body()
    response = await proxy_request("account", f"/accounts/{account_number}/deposit", "POST", dict(request.headers), body)
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.post("/api/accounts/{account_number}/withdraw")
async def withdraw_money(account_number: str, request: Request):
    """Withdraw money"""
    body = await request.body()
    response = await proxy_request("account", f"/accounts/{account_number}/withdraw", "POST", dict(request.headers), body)
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.get("/api/accounts/{account_number}/transactions")
async def get_account_transactions(account_number: str, request: Request):
    """Get account transactions"""
    response = await proxy_request("account", f"/accounts/{account_number}/transactions?{request.url.query}", "GET", dict(request.headers))
    return JSONResponse(content=response.json(), status_code=response.status_code)

# Generic service proxy for any other routes
@app.api_route("/api/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def generic_proxy(service_name: str, path: str, request: Request):
    """Generic proxy for any service route"""
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
    response = await proxy_request(service_name, f"/{path}", request.method, dict(request.headers), body)
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        init_database()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await client.aclose()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
