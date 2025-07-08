"""
Main views for the admin dashboard.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from datetime import datetime, timedelta
import json

from dashboard.models import (
    Module, ApiEndpoint, AdminUser, SystemConfig, AuditLog, SystemHealth
)

from dashboard.infrastructure.repositories import (
    DjangoModuleRepository, DjangoApiEndpointRepository,
    DjangoAdminUserRepository, DjangoSystemConfigRepository,
    DjangoAuditLogRepository, DjangoSystemHealthRepository
)

from dashboard.infrastructure.services import (
    ModuleManagementServiceImpl, ApiManagementServiceImpl, SecurityServiceImpl,
    ConfigurationServiceImpl, MonitoringServiceImpl, AuditServiceImpl
)

# Create repositories
module_repository = DjangoModuleRepository()
api_endpoint_repository = DjangoApiEndpointRepository()
admin_user_repository = DjangoAdminUserRepository()
system_config_repository = DjangoSystemConfigRepository()
audit_log_repository = DjangoAuditLogRepository()
system_health_repository = DjangoSystemHealthRepository()

# Create services
audit_service = AuditServiceImpl(audit_log_repository)
module_service = ModuleManagementServiceImpl(module_repository, audit_log_repository)
api_service = ApiManagementServiceImpl(api_endpoint_repository, module_repository, audit_log_repository)
security_service = SecurityServiceImpl(admin_user_repository, audit_log_repository)
config_service = ConfigurationServiceImpl(system_config_repository, audit_service)
monitoring_service = MonitoringServiceImpl(system_health_repository, module_repository, audit_service)


@login_required
def dashboard_home(request):
    """Render the dashboard home page."""
    # Get counts for each module status
    module_stats = {
        'total': Module.objects.count(),
        'active': Module.objects.filter(status='active').count(),
        'inactive': Module.objects.filter(status='deactivated').count(),
        'installed': Module.objects.filter(status='installed').count(),
        'failed': Module.objects.filter(status='failed').count(),
        'maintenance': Module.objects.filter(status='maintenance').count(),
    }
    
    # Get counts for API endpoints
    api_stats = {
        'total': ApiEndpoint.objects.count(),
        'enabled': ApiEndpoint.objects.filter(enabled=True).count(),
        'disabled': ApiEndpoint.objects.filter(enabled=False).count(),
    }
    
    # Get latest audit logs
    recent_logs = AuditLog.objects.all().order_by('-timestamp')[:10]
    
    # Get system health summary
    components = SystemHealth.objects.values('component').distinct()
    health_summary = []
    
    for component_dict in components:
        component = component_dict['component']
        latest = SystemHealth.objects.filter(component=component).order_by('-timestamp').first()
        if latest:
            health_summary.append(latest)
    
    # Build context for the template
    context = {
        'module_stats': module_stats,
        'api_stats': api_stats,
        'recent_logs': recent_logs,
        'health_summary': health_summary,
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required
def module_list(request):
    """Render the module list page."""
    modules = Module.objects.all()
    return render(request, 'dashboard/modules/list.html', {'modules': modules})


@login_required
def module_detail(request, module_id):
    """Render the module detail page."""
    module = Module.objects.get(id=module_id)
    endpoints = ApiEndpoint.objects.filter(module=module)
    configs = SystemConfig.objects.filter(module=module)
    
    # Get dependency status
    try:
        dependency_status = module_service.check_dependencies(module_id)
    except ValueError:
        dependency_status = {}
    
    context = {
        'module': module,
        'endpoints': endpoints,
        'configs': configs,
        'dependency_status': dependency_status,
    }
    
    return render(request, 'dashboard/modules/detail.html', context)


@login_required
@require_http_methods(["POST"])
def toggle_module(request, module_id):
    """Toggle a module's status."""
    try:
        enabled = request.POST.get('enabled') == 'true'
        module_service.toggle_module(module_id, enabled, str(request.user.id))
        messages.success(request, f"Module {'enabled' if enabled else 'disabled'} successfully")
    except ValueError as e:
        messages.error(request, str(e))
    
    return redirect('module_detail', module_id=module_id)


@login_required
def endpoint_list(request):
    """Render the API endpoint list page."""
    module_id = request.GET.get('module')
    
    if module_id:
        endpoints = ApiEndpoint.objects.filter(module_id=module_id)
    else:
        endpoints = ApiEndpoint.objects.all()
    
    modules = Module.objects.all()
    
    context = {
        'endpoints': endpoints,
        'modules': modules,
        'selected_module': module_id,
    }
    
    return render(request, 'dashboard/endpoints/list.html', context)


@login_required
@require_http_methods(["POST"])
def toggle_endpoint(request, endpoint_id):
    """Toggle an API endpoint's status."""
    try:
        enabled = request.POST.get('enabled') == 'true'
        api_service.toggle_endpoint(endpoint_id, enabled, str(request.user.id))
        messages.success(request, f"API endpoint {'enabled' if enabled else 'disabled'} successfully")
    except ValueError as e:
        messages.error(request, str(e))
    
    return redirect('endpoint_list')


@login_required
def audit_logs(request):
    """Render the audit logs page."""
    # Get filter parameters
    user_id = request.GET.get('user')
    resource_type = request.GET.get('resource_type')
    action = request.GET.get('action')
    severity = request.GET.get('severity')
    
    # Build query
    logs = AuditLog.objects.all().order_by('-timestamp')
    
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    if resource_type:
        logs = logs.filter(resource_type=resource_type)
    
    if action:
        logs = logs.filter(action=action)
    
    if severity:
        logs = logs.filter(severity=severity)
    
    # Pagination
    page_size = 20
    page = int(request.GET.get('page', 1))
    start = (page - 1) * page_size
    end = start + page_size
    
    total_logs = logs.count()
    logs = logs[start:end]
    
    # Get users for filter dropdown
    users = AdminUser.objects.all()
    
    context = {
        'logs': logs,
        'users': users,
        'total_logs': total_logs,
        'current_page': page,
        'total_pages': (total_logs + page_size - 1) // page_size,
        'filters': {
            'user_id': user_id,
            'resource_type': resource_type,
            'action': action,
            'severity': severity,
        },
    }
    
    return render(request, 'dashboard/audit/logs.html', context)


@login_required
def system_health(request):
    """Render the system health monitoring page."""
    # Get latest system health data
    latest_health = system_health_repository.get_latest_health_status()
    
    if not latest_health:
        # Create default health object if none exists
        latest_health = SystemHealth(
            status="UNKNOWN",
            cpu_usage=0,
            memory_usage=0,
            disk_usage=0,
            average_response_time=0,
            timestamp=datetime.now()
        )
    
    # Get health history for charts (last 24 hours)
    health_history = system_health_repository.get_health_history(1)
    
    # Prepare chart data
    timestamp_labels = []
    cpu_history = []
    memory_history = []
    response_time_history = []
    
    for health in health_history:
        timestamp_labels.append(health.timestamp.strftime('%H:%M'))
        cpu_history.append(health.cpu_usage)
        memory_history.append(health.memory_usage)
        response_time_history.append(health.average_response_time)
    
    # Get module health data
    module_health = monitoring_service.check_all_modules_health()
    
    # Add status classes for UI
    for module in module_health:
        if module['status'] == 'HEALTHY':
            module['status_class'] = 'success'
        elif module['status'] == 'DEGRADED':
            module['status_class'] = 'warning'
        else:
            module['status_class'] = 'danger'
    
    # Determine overall health status class for UI
    if latest_health.status == 'HEALTHY':
        health_status_class = 'success'
    elif latest_health.status == 'DEGRADED':
        health_status_class = 'warning'
    else:
        health_status_class = 'danger'
    
    context = {
        'system_health': latest_health,
        'health_status_class': health_status_class,
        'module_health': module_health,
        'timestamp_labels': json.dumps(timestamp_labels),
        'cpu_history': json.dumps(cpu_history),
        'memory_history': json.dumps(memory_history),
        'response_time_history': json.dumps(response_time_history)
    }
    
    return render(request, 'dashboard/monitoring/health.html', context)


@login_required
def system_config(request):
    """Render the system configuration page."""
    # Get all configs
    all_configs = system_config_repository.get_all_configs()
    
    # Group configs by category
    grouped_configs = {}
    existing_categories = set()
    
    for config in all_configs:
        category = config.category or 'General'
        existing_categories.add(category)
        
        if category not in grouped_configs:
            grouped_configs[category] = []
        
        grouped_configs[category].append(config)
    
    context = {
        'grouped_configs': grouped_configs,
        'existing_categories': sorted(existing_categories)
    }
    
    return render(request, 'dashboard/config/system_config.html', context)


def login_view(request):
    """Render the login page."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard_home')
        else:
            messages.error(request, "Invalid username or password")
    
    return render(request, 'dashboard/auth/login.html')


@login_required
def logout_view(request):
    """Handle logout."""
    logout(request)
    return redirect('login')
