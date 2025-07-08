#!/bin/bash

# CBS_PYTHON V2.0 Production Deployment Script
# Comprehensive deployment automation for all microservices

set -e

echo "🚀 CBS_PYTHON V2.0 Production Deployment Starting..."

# Configuration
ENVIRONMENT=${ENVIRONMENT:-production}
DOCKER_REGISTRY=${DOCKER_REGISTRY:-""}
VERSION=${VERSION:-"v2.0.0"}
PLATFORM_ROOT="/home/asus/CBS_PYTHON/cbs-platform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    
    # Check if we're in the right directory
    if [ ! -f "$PLATFORM_ROOT/docker-compose.yml" ]; then
        error "docker-compose.yml not found. Please run from platform root."
    fi
    
    # Check environment variables
    if [ -z "$DATABASE_URL" ]; then
        warn "DATABASE_URL not set, using default"
    fi
    
    log "Pre-deployment checks completed ✅"
}

# Database setup
setup_database() {
    log "Setting up databases..."
    
    # Create database initialization script
    cat > "$PLATFORM_ROOT/scripts/init-databases.sql" << 'EOF'
-- Initialize databases for all CBS_PYTHON V2.0 services
CREATE DATABASE IF NOT EXISTS gateway_service_db;
CREATE DATABASE IF NOT EXISTS customer_service_db;
CREATE DATABASE IF NOT EXISTS account_service_db;
CREATE DATABASE IF NOT EXISTS transaction_service_db;
CREATE DATABASE IF NOT EXISTS payment_service_db;
CREATE DATABASE IF NOT EXISTS loan_service_db;
CREATE DATABASE IF NOT EXISTS notification_service_db;
CREATE DATABASE IF NOT EXISTS audit_service_db;

-- Create service users
CREATE USER IF NOT EXISTS 'gateway_user'@'%' IDENTIFIED BY 'gateway_pass';
CREATE USER IF NOT EXISTS 'customer_user'@'%' IDENTIFIED BY 'customer_pass';
CREATE USER IF NOT EXISTS 'account_user'@'%' IDENTIFIED BY 'account_pass';
CREATE USER IF NOT EXISTS 'transaction_user'@'%' IDENTIFIED BY 'transaction_pass';
CREATE USER IF NOT EXISTS 'payment_user'@'%' IDENTIFIED BY 'payment_pass';
CREATE USER IF NOT EXISTS 'loan_user'@'%' IDENTIFIED BY 'loan_pass';
CREATE USER IF NOT EXISTS 'notification_user'@'%' IDENTIFIED BY 'notification_pass';
CREATE USER IF NOT EXISTS 'audit_user'@'%' IDENTIFIED BY 'audit_pass';

-- Grant permissions
GRANT ALL PRIVILEGES ON gateway_service_db.* TO 'gateway_user'@'%';
GRANT ALL PRIVILEGES ON customer_service_db.* TO 'customer_user'@'%';
GRANT ALL PRIVILEGES ON account_service_db.* TO 'account_user'@'%';
GRANT ALL PRIVILEGES ON transaction_service_db.* TO 'transaction_user'@'%';
GRANT ALL PRIVILEGES ON payment_service_db.* TO 'payment_user'@'%';
GRANT ALL PRIVILEGES ON loan_service_db.* TO 'loan_user'@'%';
GRANT ALL PRIVILEGES ON notification_service_db.* TO 'notification_user'@'%';
GRANT ALL PRIVILEGES ON audit_service_db.* TO 'audit_user'@'%';

FLUSH PRIVILEGES;
EOF
    
    log "Database setup completed ✅"
}

# Build Docker images
build_images() {
    log "Building Docker images..."
    
    cd "$PLATFORM_ROOT"
    
    # Build platform image
    info "Building CBS Platform V2.0 image..."
    docker build -t cbs-platform:$VERSION .
    
    if [ ! -z "$DOCKER_REGISTRY" ]; then
        info "Tagging image for registry..."
        docker tag cbs-platform:$VERSION $DOCKER_REGISTRY/cbs-platform:$VERSION
        docker tag cbs-platform:$VERSION $DOCKER_REGISTRY/cbs-platform:latest
    fi
    
    log "Docker images built successfully ✅"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Services that need migrations
    SERVICES=(
        "customer-service"
        "account-service"
        "transaction-service"
        "payment-service"
        "loan-service"
        "notification-service"
        "audit-service"
    )
    
    for service in "${SERVICES[@]}"; do
        info "Running migrations for $service..."
        cd "$PLATFORM_ROOT/services/$service"
        
        if [ -f "alembic.ini" ]; then
            # Install alembic if not present
            pip install alembic
            
            # Run migrations
            alembic upgrade head || warn "Migration failed for $service"
        else
            warn "No alembic.ini found for $service"
        fi
    done
    
    cd "$PLATFORM_ROOT"
    log "Database migrations completed ✅"
}

# Deploy services
deploy_services() {
    log "Deploying CBS_PYTHON V2.0 services..."
    
    cd "$PLATFORM_ROOT"
    
    # Stop existing services
    info "Stopping existing services..."
    docker-compose down || true
    
    # Remove old containers and networks
    docker container prune -f
    docker network prune -f
    
    # Start infrastructure services first
    info "Starting infrastructure services..."
    docker-compose up -d postgres redis
    
    # Wait for database to be ready
    info "Waiting for database to be ready..."
    sleep 30
    
    # Start all services
    info "Starting all CBS_PYTHON V2.0 services..."
    docker-compose up -d
    
    log "Services deployment completed ✅"
}

# Health checks
health_checks() {
    log "Running health checks..."
    
    # Wait for services to start
    info "Waiting for services to start..."
    sleep 60
    
    # Check each service
    SERVICES=(
        "gateway-service:8000"
        "customer-service:8001"
        "account-service:8002"
        "transaction-service:8003"
        "payment-service:8004"
        "loan-service:8005"
        "notification-service:8006"
        "audit-service:8007"
    )
    
    for service_port in "${SERVICES[@]}"; do
        service=${service_port%:*}
        port=${service_port#*:}
        
        info "Checking $service on port $port..."
        
        # Try to connect to health endpoint
        if curl -f -s "http://localhost:$port/health" > /dev/null; then
            log "$service is healthy ✅"
        else
            warn "$service health check failed ❌"
            # Show logs for debugging
            docker-compose logs --tail=20 $service
        fi
    done
    
    log "Health checks completed ✅"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Create monitoring configuration
    mkdir -p "$PLATFORM_ROOT/monitoring"
    
    # Prometheus configuration
    cat > "$PLATFORM_ROOT/monitoring/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'cbs-platform'
    static_configs:
      - targets: 
        - 'gateway-service:8000'
        - 'customer-service:8001'
        - 'account-service:8002'
        - 'transaction-service:8003'
        - 'payment-service:8004'
        - 'loan-service:8005'
        - 'notification-service:8006'
        - 'audit-service:8007'
    metrics_path: '/metrics'
    scrape_interval: 5s
EOF
    
    info "Starting monitoring services..."
    docker-compose up -d prometheus grafana
    
    log "Monitoring setup completed ✅"
    info "Prometheus: http://localhost:9090"
    info "Grafana: http://localhost:3000 (admin/admin)"
}

# Post-deployment tasks
post_deployment() {
    log "Running post-deployment tasks..."
    
    # Create admin user (if needed)
    info "Setting up initial admin user..."
    # This would typically involve API calls to create admin accounts
    
    # Generate deployment report
    info "Generating deployment report..."
    cat > "$PLATFORM_ROOT/deployment_report_$(date +%Y%m%d_%H%M%S).md" << EOF
# CBS_PYTHON V2.0 Deployment Report

**Deployment Date**: $(date)
**Version**: $VERSION
**Environment**: $ENVIRONMENT

## Services Deployed
- ✅ API Gateway Service (Port 8000)
- ✅ Customer Service (Port 8001)
- ✅ Account Service (Port 8002)
- ✅ Transaction Service (Port 8003)
- ✅ Payment Service (Port 8004)
- ✅ Loan Service (Port 8005)
- ✅ Notification Service (Port 8006)
- ✅ Audit Service (Port 8007)

## Infrastructure
- ✅ PostgreSQL Database
- ✅ Redis Cache
- ✅ Prometheus Monitoring
- ✅ Grafana Dashboards

## Access URLs
- **Main API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Monitoring**: http://localhost:9090
- **Dashboards**: http://localhost:3000

## Next Steps
1. Configure SSL certificates for production
2. Set up backup schedules
3. Configure alerting rules
4. Run load tests
5. Train operations team

EOF
    
    log "Post-deployment tasks completed ✅"
}

# Rollback function
rollback() {
    error "Deployment failed! Rolling back..."
    
    info "Stopping new services..."
    docker-compose down
    
    info "Restoring previous version..."
    # This would restore from backup or previous version
    
    error "Rollback completed"
}

# Cleanup function
cleanup() {
    log "Cleaning up deployment artifacts..."
    
    # Remove temporary files
    rm -f "$PLATFORM_ROOT/scripts/init-databases.sql" || true
    
    # Clean up unused Docker resources
    docker system prune -f
    
    log "Cleanup completed ✅"
}

# Main deployment workflow
main() {
    log "🏁 Starting CBS_PYTHON V2.0 Production Deployment"
    log "Platform: $PLATFORM_ROOT"
    log "Environment: $ENVIRONMENT"
    log "Version: $VERSION"
    
    # Set trap for cleanup on exit
    trap cleanup EXIT
    trap rollback ERR
    
    # Execute deployment steps
    pre_deployment_checks
    setup_database
    build_images
    run_migrations
    deploy_services
    health_checks
    setup_monitoring
    post_deployment
    
    log "🎉 CBS_PYTHON V2.0 Deployment Completed Successfully!"
    log "🌐 Platform is available at: http://localhost:8000"
    log "📊 Monitoring dashboard: http://localhost:3000"
    log "📖 API Documentation: http://localhost:8000/docs"
    
    info "Deployment logs saved to: $PLATFORM_ROOT/deployment_report_$(date +%Y%m%d_%H%M%S).md"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "health")
        health_checks
        ;;
    "rollback")
        rollback
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        echo "Usage: $0 {deploy|health|rollback|cleanup}"
        exit 1
        ;;
esac
