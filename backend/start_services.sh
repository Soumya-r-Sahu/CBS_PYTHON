#!/bin/bash

# Core Banking System V3.0 - Service Startup Script

echo "🚀 Starting Core Banking System V3.0..."

# Function to check if a port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $1 is already in use"
        return 1
    else
        echo "✅ Port $1 is available"
        return 0
    fi
}

# Function to start a service
start_service() {
    local service_name=$1
    local port=$2
    local file_path=$3
    
    echo "🔧 Starting $service_name on port $port..."
    
    if check_port $port; then
        cd /home/asus/CBS_PYTHON/backend/services/$service_name
        uvicorn main:app --host 0.0.0.0 --port $port --reload &
        echo "✅ $service_name started on port $port"
    else
        echo "❌ Cannot start $service_name - port $port is in use"
    fi
}

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "❌ uvicorn not found. Installing..."
    pip install uvicorn
fi

echo "📋 Checking ports availability..."

# Check all required ports
check_port 8000  # API Gateway
check_port 8001  # Auth Service
check_port 8002  # Account Service
check_port 8003  # Customer Service
check_port 8004  # Transaction Service
check_port 8005  # Payment Service
check_port 8006  # Loan Service
check_port 8007  # Notification Service
check_port 8008  # Reporting Service

echo ""
echo "🔧 Starting services..."

# Start all services
start_service "auth_service" 8001
sleep 2

start_service "customer_service" 8003
sleep 2

start_service "account_service" 8002
sleep 2

# Start API Gateway last
echo "🔧 Starting API Gateway on port 8000..."
if check_port 8000; then
    cd /home/asus/CBS_PYTHON/backend/api_gateway
    uvicorn gateway:app --host 0.0.0.0 --port 8000 --reload &
    echo "✅ API Gateway started on port 8000"
fi

echo ""
echo "🎉 Core Banking System V3.0 startup complete!"
echo ""
echo "📊 Service Status:"
echo "  🔐 Auth Service:      http://localhost:8001"
echo "  👥 Customer Service:  http://localhost:8003"
echo "  💳 Account Service:   http://localhost:8002"
echo "  🌐 API Gateway:       http://localhost:8000"
echo ""
echo "📖 API Documentation:"
echo "  🔐 Auth API:          http://localhost:8001/docs"
echo "  👥 Customer API:      http://localhost:8003/docs"
echo "  💳 Account API:       http://localhost:8002/docs"
echo "  🌐 Gateway API:       http://localhost:8000/docs"
echo ""
echo "🔍 Health Checks:"
echo "  🩺 Overall Health:    http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
wait
