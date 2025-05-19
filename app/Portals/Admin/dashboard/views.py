from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
import json
import logging

from dashboard.application.services.admin_services import ModuleManagementService, SystemMonitoringApplication
from dashboard.infrastructure.repositories.admin_repositories import (
    InMemoryModuleRepository,
    InMemoryApiEndpointRepository,
    InMemoryFeatureFlagRepository,
    PsutilSystemMonitoringService
)

# Set up logging
logger = logging.getLogger(__name__)

# Initialize services
module_repo = InMemoryModuleRepository()
endpoint_repo = InMemoryApiEndpointRepository()
feature_repo = InMemoryFeatureFlagRepository()
monitoring_service = PsutilSystemMonitoringService()

module_service = ModuleManagementService(module_repo, endpoint_repo, feature_repo)
system_monitoring = SystemMonitoringApplication(monitoring_service)

@login_required
def dashboard(request):
    """Admin dashboard view"""
    # Get system health data
    health_data = system_monitoring.get_system_health_dashboard()
    
    # Get all modules
    modules = module_service.get_all_modules()
    
    context = {
        'health_data': health_data,
        'modules': modules,
        'page_title': 'Admin Dashboard'
    }
    
    return render(request, 'dashboard/index.html', context)

@login_required
def module_management(request):
    """Module management view"""
    modules = module_service.get_all_modules()
    
    context = {
        'modules': modules,
        'page_title': 'Module Management'
    }
    
    return render(request, 'dashboard/modules/index.html', context)

@login_required
def module_detail(request, module_id):
    """Module detail view"""
    module_details = module_service.get_module_details(module_id)
    
    if not module_details:
        messages.error(request, f"Module {module_id} not found")
        return redirect('module_management')
    
    context = {
        'module': module_details.get('module'),
        'endpoints': module_details.get('endpoints', []),
        'features': module_details.get('features', []),
        'page_title': f'Module: {module_details.get("module").name}'
    }
    
    return render(request, 'dashboard/modules/detail.html', context)

@login_required
@require_POST
def toggle_module(request, module_id):
    """Toggle module active status"""
    try:
        data = json.loads(request.body)
        active = data.get('active', False)
        
        module = module_service.toggle_module(module_id, active)
        
        return JsonResponse({
            'success': True,
            'module': {
                'id': module.id,
                'name': module.name,
                'status': module.status.value
            }
        })
    except Exception as e:
        logger.error(f"Error toggling module {module_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_POST
def toggle_feature(request, module_id, feature_name):
    """Toggle feature flag"""
    try:
        data = json.loads(request.body)
        enabled = data.get('enabled', False)
        
        feature = module_service.toggle_feature(feature_name, module_id, enabled)
        
        return JsonResponse({
            'success': True,
            'feature': {
                'name': feature.name,
                'module_id': feature.module_id,
                'enabled': feature.enabled
            }
        })
    except Exception as e:
        logger.error(f"Error toggling feature {feature_name}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_POST
def toggle_endpoint(request, endpoint_id):
    """Toggle API endpoint"""
    try:
        data = json.loads(request.body)
        enabled = data.get('enabled', False)
        
        endpoint = module_service.toggle_endpoint(endpoint_id, enabled)
        
        return JsonResponse({
            'success': True,
            'endpoint': {
                'id': endpoint.id,
                'path': endpoint.path,
                'method': endpoint.method,
                'enabled': endpoint.enabled
            }
        })
    except Exception as e:
        logger.error(f"Error toggling endpoint {endpoint_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
def system_health(request):
    """System health view"""
    health_data = system_monitoring.get_system_health_dashboard()
    
    context = {
        'health_data': health_data,
        'page_title': 'System Health'
    }
    
    return render(request, 'dashboard/system/health.html', context)

@login_required
def api_management(request):
    """API management view"""
    endpoints = endpoint_repo.get_all_endpoints()
    
    context = {
        'endpoints': endpoints,
        'page_title': 'API Management'
    }
    
    return render(request, 'dashboard/api/index.html', context)
