"""
Admin API endpoints for module registration and management.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404

from dashboard.models import (
    Module, ApiEndpoint, FeatureFlag, SystemConfig, 
    AuditLog, SystemHealth, AuditLogAction, AuditLogSeverity
)
from dashboard.presentation.api.serializers import (    ModuleSerializer, ApiEndpointSerializer, FeatureFlagSerializer,
    SystemConfigSerializer, SystemHealthSerializer
)
from django.contrib.auth.decorators import user_passes_test

import json
import logging

logger = logging.getLogger(__name__)

# Define a simple IsAdminUser permission check function
def IsAdminUser(view_func):
    """Decorator that checks if the user is an admin"""
    return user_passes_test(lambda u: u.is_staff)(view_func)


class ModuleViewSet(viewsets.ModelViewSet):
    """API endpoint for managing modules."""
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Toggle a module's status between active and deactivated."""
        module = self.get_object()
        
        if module.status == 'active':
            module.status = 'deactivated'
        elif module.status == 'deactivated' or module.status == 'installed':
            module.status = 'active'
        else:
            return Response(
                {"error": f"Cannot toggle module in {module.status} state"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        module.save()
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action=AuditLogAction.ENABLE if module.status == 'active' else AuditLogAction.DISABLE,
            resource_type='module',
            resource_id=module.id,
            details={'status': module.status}
        )
        
        return Response(ModuleSerializer(module).data)
    
    @action(detail=True, methods=['post'])
    def configure(self, request, pk=None):
        """Update module configuration."""
        module = self.get_object()
        
        # Update module properties from request data
        for key, value in request.data.items():
            if hasattr(module, key) and key != 'id':
                setattr(module, key, value)
        
        module.save()
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action=AuditLogAction.CONFIGURE,
            resource_type='module',
            resource_id=module.id,
            details=request.data
        )
        
        return Response(ModuleSerializer(module).data)


class ModuleRegistrationView(APIView):
    """API endpoint for external module registration."""
    
    def post(self, request, format=None):
        """
        Register or update a module.
        
        This endpoint allows modules to register themselves with the Admin module.
        
        Expected payload:
        {
            "id": "module_id",
            "name": "Module Name",
            "version": "1.0.0",
            "description": "Module description",
            "dependencies": ["other_module_id", ...]
        }
        """
        try:
            # Validate the authentication key from request headers
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return Response(
                    {"error": "No API key provided"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Here you would validate the API key against registered keys
            # For now, we'll use a simple check
            # TODO: Implement proper API key validation
            if api_key != "dummy-key":  # Replace with actual key validation
                return Response(
                    {"error": "Invalid API key"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Create or update the module
            module_id = request.data.get('id')
            if not module_id:
                return Response(
                    {"error": "Module ID is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            module, created = Module.objects.update_or_create(
                id=module_id,
                defaults={
                    'name': request.data.get('name', f"Module {module_id}"),
                    'version': request.data.get('version', '1.0.0'),
                    'description': request.data.get('description', ''),
                    'dependencies': request.data.get('dependencies', []),
                    # Keep the current status if it exists, otherwise set to INSTALLED
                    'status': Module.objects.get(id=module_id).status if not created else 'installed'
                }
            )
            
            # Log the action
            AuditLog.objects.create(
                action=AuditLogAction.CREATE if created else AuditLogAction.UPDATE,
                resource_type='module',
                resource_id=module.id,
                details=request.data
            )
            
            return Response(
                {
                    "status": "success",
                    "message": "Module registered successfully",
                    "module": ModuleSerializer(module).data
                },
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        
        except Exception as e:
            logger.error(f"Error registering module: {str(e)}")
            return Response(
                {"error": f"Failed to register module: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ApiEndpointRegistrationView(APIView):
    """API endpoint for registering module API endpoints."""
    
    def post(self, request, format=None):
        """
        Register or update API endpoints for a module.
        
        Expected payload:
        {
            "module_id": "module_id",
            "endpoints": [
                {
                    "path": "/api/endpoint",
                    "method": "GET",
                    "description": "Endpoint description",
                    "auth_required": true,
                    "rate_limit": 100
                },
                ...
            ]
        }
        """
        try:
            # Validate the authentication key from request headers
            api_key = request.headers.get('X-API-Key')
            module_id = request.data.get('module_id')
            
            if not api_key:
                return Response(
                    {"error": "No API key provided"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # TODO: Implement proper API key validation
            if api_key != "dummy-key":
                return Response(
                    {"error": "Invalid API key"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            if not module_id:
                return Response(
                    {"error": "Module ID is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the module or return 404
            module = get_object_or_404(Module, id=module_id)
            
            # Process the endpoints
            endpoints_data = request.data.get('endpoints', [])
            created_count = 0
            updated_count = 0
            
            for endpoint_data in endpoints_data:
                path = endpoint_data.get('path')
                method = endpoint_data.get('method')
                
                if not path or not method:
                    continue
                
                # Generate a unique ID for the endpoint
                endpoint_id = f"{module_id}_{method}_{path}".replace('/', '_')
                
                endpoint, created = ApiEndpoint.objects.update_or_create(
                    id=endpoint_id,
                    defaults={
                        'path': path,
                        'module': module,
                        'method': method,
                        'enabled': endpoint_data.get('enabled', True),
                        'auth_required': endpoint_data.get('auth_required', True),
                        'rate_limit': endpoint_data.get('rate_limit'),
                        'description': endpoint_data.get('description', '')
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            # Log the action
            AuditLog.objects.create(
                action=AuditLogAction.UPDATE,
                resource_type='api_endpoints',
                resource_id=module_id,
                details={
                    'created_count': created_count,
                    'updated_count': updated_count
                }
            )
            
            return Response({
                "status": "success",
                "message": f"API endpoints registered: {created_count} created, {updated_count} updated",
                "module_id": module_id
            })
        
        except Exception as e:
            logger.error(f"Error registering API endpoints: {str(e)}")
            return Response(
                {"error": f"Failed to register API endpoints: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FeatureFlagRegistrationView(APIView):
    """API endpoint for registering module feature flags."""
    
    def post(self, request, format=None):
        """
        Register or update feature flags for a module.
        
        Expected payload:
        {
            "module_id": "module_id",
            "features": [
                {
                    "name": "feature_name",
                    "description": "Feature description",
                    "enabled": false,
                    "affects_endpoints": ["endpoint_id", ...]
                },
                ...
            ]
        }
        """
        try:
            # Validate the authentication key from request headers
            api_key = request.headers.get('X-API-Key')
            module_id = request.data.get('module_id')
            
            if not api_key:
                return Response(
                    {"error": "No API key provided"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # TODO: Implement proper API key validation
            if api_key != "dummy-key":
                return Response(
                    {"error": "Invalid API key"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            if not module_id:
                return Response(
                    {"error": "Module ID is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the module or return 404
            module = get_object_or_404(Module, id=module_id)
            
            # Process the feature flags
            features_data = request.data.get('features', [])
            created_count = 0
            updated_count = 0
            
            for feature_data in features_data:
                name = feature_data.get('name')
                
                if not name:
                    continue
                
                # Generate a unique ID for the feature flag
                feature_id = f"{module_id}_{name}"
                
                feature, created = FeatureFlag.objects.update_or_create(
                    id=feature_id,
                    defaults={
                        'name': name,
                        'module': module,
                        'description': feature_data.get('description', ''),
                        'enabled': feature_data.get('enabled', False),
                        'affects_endpoints': feature_data.get('affects_endpoints', [])
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            # Log the action
            AuditLog.objects.create(
                action=AuditLogAction.UPDATE,
                resource_type='feature_flags',
                resource_id=module_id,
                details={
                    'created_count': created_count,
                    'updated_count': updated_count
                }
            )
            
            return Response({
                "status": "success",
                "message": f"Feature flags registered: {created_count} created, {updated_count} updated",
                "module_id": module_id
            })
        
        except Exception as e:
            logger.error(f"Error registering feature flags: {str(e)}")
            return Response(
                {"error": f"Failed to register feature flags: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConfigurationRegistrationView(APIView):
    """API endpoint for registering module configurations."""
    
    def post(self, request, format=None):
        """
        Register or update configurations for a module.
        
        Expected payload:
        {
            "module_id": "module_id",
            "configurations": [
                {
                    "key": "config_key",
                    "value": "config_value",
                    "type": "module",
                    "description": "Configuration description",
                    "is_sensitive": false,
                    "allowed_values": ["value1", "value2", ...]
                },
                ...
            ]
        }
        """
        try:
            # Validate the authentication key from request headers
            api_key = request.headers.get('X-API-Key')
            module_id = request.data.get('module_id')
            
            if not api_key:
                return Response(
                    {"error": "No API key provided"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # TODO: Implement proper API key validation
            if api_key != "dummy-key":
                return Response(
                    {"error": "Invalid API key"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            if not module_id:
                return Response(
                    {"error": "Module ID is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the module or return 404
            module = get_object_or_404(Module, id=module_id)
            
            # Process the configurations
            configs_data = request.data.get('configurations', [])
            created_count = 0
            updated_count = 0
            
            for config_data in configs_data:
                key = config_data.get('key')
                
                if not key:
                    continue
                
                # Generate a unique ID for the configuration
                config_id = f"{module_id}_{key}"
                
                config, created = SystemConfig.objects.update_or_create(
                    id=config_id,
                    defaults={
                        'key': key,
                        'module': module,
                        'value': config_data.get('value', {}),
                        'type': config_data.get('type', 'module'),
                        'description': config_data.get('description', ''),
                        'is_sensitive': config_data.get('is_sensitive', False),
                        'allowed_values': config_data.get('allowed_values')
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            # Log the action
            AuditLog.objects.create(
                action=AuditLogAction.UPDATE,
                resource_type='configurations',
                resource_id=module_id,
                details={
                    'created_count': created_count,
                    'updated_count': updated_count
                }
            )
            
            return Response({
                "status": "success",
                "message": f"Configurations registered: {created_count} created, {updated_count} updated",
                "module_id": module_id
            })
        
        except Exception as e:
            logger.error(f"Error registering configurations: {str(e)}")
            return Response(
                {"error": f"Failed to register configurations: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HealthMetricsRegistrationView(APIView):
    """API endpoint for sending module health metrics."""
    
    def post(self, request, format=None):
        """
        Send health metrics for a module.
        
        Expected payload:
        {
            "module_id": "module_id",
            "health": {
                "status": "healthy",
                "metrics": {
                    "cpu": 0.5,
                    "memory": 0.3,
                    ...
                },
                "details": {
                    "message": "All systems operational"
                },
                "alerts": ["Warning: High CPU usage"]
            }
        }
        """
        try:
            # Validate the authentication key from request headers
            api_key = request.headers.get('X-API-Key')
            module_id = request.data.get('module_id')
            
            if not api_key:
                return Response(
                    {"error": "No API key provided"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # TODO: Implement proper API key validation
            if api_key != "dummy-key":
                return Response(
                    {"error": "Invalid API key"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            if not module_id:
                return Response(
                    {"error": "Module ID is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the health data
            health_data = request.data.get('health', {})
            status_value = health_data.get('status', 'unknown')
            metrics = health_data.get('metrics', {})
            details = health_data.get('details', {})
            alerts = health_data.get('alerts', [])
            
            # Create the health record
            health = SystemHealth.objects.create(
                component=module_id,
                status=status_value,
                metrics=metrics,
                details=details,
                alerts=alerts
            )
            
            # If there are alerts, log them
            if alerts:
                AuditLog.objects.create(
                    action=AuditLogAction.CREATE,
                    resource_type='health_alert',
                    resource_id=module_id,
                    severity=AuditLogSeverity.WARNING if status_value != 'critical' else AuditLogSeverity.CRITICAL,
                    details={
                        'status': status_value,
                        'alerts': alerts
                    }
                )
            
            return Response({
                "status": "success",
                "message": "Health metrics recorded",
                "module_id": module_id,
                "health_id": health.id
            })
        
        except Exception as e:
            logger.error(f"Error recording health metrics: {str(e)}")
            return Response(
                {"error": f"Failed to record health metrics: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
