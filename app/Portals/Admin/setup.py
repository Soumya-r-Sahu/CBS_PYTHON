#!/usr/bin/env python
"""
Setup script for the CBS Admin module.
This script will:
1. Create database migrations
2. Apply migrations to the database
3. Create a default admin user if none exists
"""
import os
import sys
import django
from django.core.management import call_command

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cbs_admin.settings')
django.setup()

from django.contrib.auth.models import User
from dashboard.models import AdminUser, SystemConfig, Module, ApiEndpoint
from dashboard.domain.entities.system_health import HealthStatus

def setup_database():
    """Create and apply database migrations"""
    print("Creating database migrations...")
    call_command('makemigrations')
    
    print("Applying migrations to database...")
    call_command('migrate')
    
    return True

def create_default_admin():
    """Create a default admin user if no users exist"""
    if User.objects.count() == 0:
        print("Creating default admin user...")
        
        # Create Django auth user
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='Admin@123'  # This should be changed immediately
        )
        
        # Create AdminUser profile
        AdminUser.objects.create(
            user=admin_user,
            role='admin',
            permissions='["*"]',  # Full permissions
            status='active'
        )
        
        print("Default admin user created with username 'admin' and password 'Admin@123'")
        print("IMPORTANT: Please change this password immediately after first login!")
    else:
        print("Admin users already exist, skipping default user creation.")
    
    return True

def create_default_configs():
    """Create default system configurations"""
    if SystemConfig.objects.count() == 0:
        print("Creating default system configurations...")
        
        default_configs = [
            {
                'key': 'SYSTEM_NAME',
                'value': 'CBS Admin',
                'category': 'System',
                'description': 'The name of the system',
                'data_type': 'STRING',
            },
            {
                'key': 'APP_DEBUG_MODE',
                'value': 'True',
                'category': 'System',
                'description': 'Enable debug mode for development',
                'data_type': 'BOOLEAN',
            },
            {
                'key': 'SESSION_TIMEOUT',
                'value': '3600',
                'category': 'Security',
                'description': 'Session timeout in seconds',
                'data_type': 'INTEGER',
            },
            {
                'key': 'MAX_LOGIN_ATTEMPTS',
                'value': '5',
                'category': 'Security',
                'description': 'Maximum failed login attempts before lockout',
                'data_type': 'INTEGER',
            },
            {
                'key': 'ALLOWED_API_ORIGINS',
                'value': '["localhost", "127.0.0.1"]',
                'category': 'API',
                'description': 'Allowed origins for API requests',
                'data_type': 'JSON',
            },
        ]
        
        for config in default_configs:
            SystemConfig.objects.create(**config)
        
        print(f"Created {len(default_configs)} default configurations.")
    else:
        print("System configurations already exist, skipping defaults creation.")
    
    return True

def create_sample_modules():
    """Create sample modules for demonstration"""
    if Module.objects.count() == 0:
        print("Creating sample modules...")
        
        sample_modules = [
            {
                'id': 'core',
                'name': 'Core Module',
                'version': '1.0.0',
                'status': 'active',
                'description': 'Core system functionality',
                'dependencies': '[]',
                'entry_point': 'core.main',
                'icon': 'fa-cogs'
            },
            {
                'id': 'users',
                'name': 'User Management',
                'version': '1.0.0',
                'status': 'active',
                'description': 'User management functionality',
                'dependencies': '["core"]',
                'entry_point': 'users.main',
                'icon': 'fa-users'
            },
            {
                'id': 'reporting',
                'name': 'Reporting Module',
                'version': '0.9.0',
                'status': 'installed',
                'description': 'Reporting and analytics',
                'dependencies': '["core", "users"]',
                'entry_point': 'reporting.main',
                'icon': 'fa-chart-bar'
            }
        ]
        
        for module_data in sample_modules:
            module = Module.objects.create(**module_data)
            
            # Create sample endpoints for each module
            if module.id == 'core':
                ApiEndpoint.objects.create(
                    id='core-health',
                    name='System Health Check',
                    path='/api/system/health',
                    method='GET',
                    enabled=True,
                    module=module,
                    requires_auth=True,
                    rate_limit=100
                )
                ApiEndpoint.objects.create(
                    id='core-status',
                    name='System Status',
                    path='/api/system/status',
                    method='GET',
                    enabled=True,
                    module=module,
                    requires_auth=True,
                    rate_limit=100
                )
            elif module.id == 'users':
                ApiEndpoint.objects.create(
                    id='users-list',
                    name='List Users',
                    path='/api/users',
                    method='GET',
                    enabled=True,
                    module=module,
                    requires_auth=True,
                    rate_limit=50
                )
                ApiEndpoint.objects.create(
                    id='users-create',
                    name='Create User',
                    path='/api/users',
                    method='POST',
                    enabled=True,
                    module=module,
                    requires_auth=True,
                    rate_limit=10
                )
            elif module.id == 'reporting':
                ApiEndpoint.objects.create(
                    id='reports-generate',
                    name='Generate Report',
                    path='/api/reports/generate',
                    method='POST',
                    enabled=False,  # Disabled as module is not active
                    module=module,
                    requires_auth=True,
                    rate_limit=5
                )
        
        print(f"Created {len(sample_modules)} sample modules with API endpoints.")
    else:
        print("Modules already exist, skipping sample creation.")
    
    return True

def create_sample_health_data():
    """Create sample health data for demonstration"""
    from dashboard.models import SystemHealth
    from datetime import datetime, timedelta
    
    if SystemHealth.objects.count() == 0:
        print("Creating sample health data...")
        
        # Generate sample health data for the past 24 hours
        now = datetime.now()
        
        for i in range(24):
            timestamp = now - timedelta(hours=i)
            
            # Randomize a bit to make the data look realistic
            import random
            cpu = random.randint(20, 80)
            memory = random.randint(30, 70)
            disk = random.randint(40, 60)
            response_time = random.randint(50, 500)
            
            # Determine status based on metrics
            if cpu > 70 or memory > 70 or response_time > 300:
                status = HealthStatus.DEGRADED
            elif cpu > 85 or memory > 85 or response_time > 450:
                status = HealthStatus.UNHEALTHY
            else:
                status = HealthStatus.HEALTHY
            
            SystemHealth.objects.create(
                component='system',
                status=status,
                cpu_usage=cpu,
                memory_usage=memory,
                disk_usage=disk,
                average_response_time=response_time,
                timestamp=timestamp
            )
        
        print(f"Created 24 hours of sample health data.")
    else:
        print("Health data already exists, skipping sample creation.")
    
    return True

def main():
    """Main setup function"""
    print("=== CBS Admin Setup ===")
    
    try:
        setup_database()
        create_default_admin()
        create_default_configs()
        create_sample_modules()
        create_sample_health_data()
        
        print("\nSetup completed successfully!")
        print("You can now start the server with: python manage.py runserver")
        print("Access the admin panel at: http://127.0.0.1:8000/")
        print("\nDefault login credentials:")
        print("Username: admin")
        print("Password: Admin@123")
        print("IMPORTANT: Please change this password immediately after first login!")
        
    except Exception as e:
        print(f"Error during setup: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    main()
