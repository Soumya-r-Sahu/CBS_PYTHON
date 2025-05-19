"""
API views for the admin dashboard.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import json
from datetime import datetime, timedelta

from dashboard.models import Module, ApiEndpoint, AdminUser, SystemConfig, AuditLog, SystemHealth
from dashboard.presentation.api.serializers import (
    ModuleSerializer, ApiEndpointSerializer, AdminUserSerializer, 
    SystemConfigSerializer, AuditLogSerializer, SystemHealthSerializer,
    ModuleToggleRequestSerializer, ApiEndpointToggleRequestSerializer,
    RateLimitRequestSerializer, ConfigUpdateRequestSerializer,
    LoginRequestSerializer, LoginResponseSerializer, PasswordChangeRequestSerializer
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


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access the API.
    """
    def has_permission(self, request, view):
        token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1] if 'HTTP_AUTHORIZATION' in request.META else None
        
        if not token:
            return False
        
        user = security_service.validate_token(token)
        if not user:
            return False
        
        # Store the user in the request for later use
        request.user = user
        
        # Check permissions based on the view or action
        # For simplicity, we're allowing all authenticated admin users for now
        return True


class LoginView(APIView):
    """View for user login."""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Handle login requests."""
        serializer = LoginRequestSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            # Get client IP address
            ip_address = request.META.get('REMOTE_ADDR')
            
            token = security_service.authenticate_user(username, password, ip_address)
            if token:
                user = admin_user_repository.get_user_by_username(username)
                response_data = {
                    'token': token,
                    'user': AdminUserSerializer(user._user_model).data
                }
                return Response(response_data)
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    """View for changing password."""
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        """Handle password change requests."""
        serializer = PasswordChangeRequestSerializer(data=request.data)
        if serializer.is_valid():
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            
            # Get client IP address
            ip_address = request.META.get('REMOTE_ADDR')
            
            if security_service.change_password(request.user.id, old_password, new_password, ip_address):
                return Response({'message': 'Password changed successfully'})
            else:
                return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ModuleViewSet(viewsets.ModelViewSet):
    """ViewSet for modules."""
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Toggle a module."""
        module = self.get_object()
        serializer = ModuleToggleRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            enabled = serializer.validated_data['enabled']
            
            try:
                updated_module = module_service.toggle_module(module.id, enabled, request.user.id)
                return Response(ModuleSerializer(updated_module._model).data)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def restart(self, request, pk=None):
        """Restart a module."""
        module = self.get_object()
        
        try:
            success = module_service.restart_module(module.id, request.user.id)
            if success:
                return Response({'message': f'Module {module.name} restarted successfully'})
            else:
                return Response({'error': 'Failed to restart module'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def dependencies(self, request, pk=None):
        """Check module dependencies."""
        module = self.get_object()
        
        try:
            dependency_status = module_service.check_dependencies(module.id)
            return Response(dependency_status)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ApiEndpointViewSet(viewsets.ModelViewSet):
    """ViewSet for API endpoints."""
    queryset = ApiEndpoint.objects.all()
    serializer_class = ApiEndpointSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Toggle an API endpoint."""
        endpoint = self.get_object()
        serializer = ApiEndpointToggleRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            enabled = serializer.validated_data['enabled']
            
            try:
                updated_endpoint = api_service.toggle_endpoint(endpoint.id, enabled, request.user.id)
                return Response(ApiEndpointSerializer(updated_endpoint._model).data)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def rate_limit(self, request, pk=None):
        """Set the rate limit for an API endpoint."""
        endpoint = self.get_object()
        serializer = RateLimitRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            rate_limit = serializer.validated_data['rate_limit']
            
            try:
                updated_endpoint = api_service.set_rate_limit(endpoint.id, rate_limit, request.user.id)
                return Response(ApiEndpointSerializer(updated_endpoint._model).data)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_queryset(self):
        """
        Optionally restricts the returned endpoints to a given module,
        by filtering against a `module` query parameter in the URL.
        """
        queryset = ApiEndpoint.objects.all()
        module_id = self.request.query_params.get('module', None)
        if module_id is not None:
            queryset = queryset.filter(module__id=module_id)
        return queryset


class AdminUserViewSet(viewsets.ModelViewSet):
    """ViewSet for admin users."""
    queryset = AdminUser.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]


class SystemConfigViewSet(viewsets.ModelViewSet):
    """ViewSet for system configuration."""
    queryset = SystemConfig.objects.all()
    serializer_class = SystemConfigSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def update_value(self, request, pk=None):
        """Update a configuration value."""
        config = self.get_object()
        serializer = ConfigUpdateRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            value = serializer.validated_data['value']
            
            # Update the config
            config.value = value
            
            # Save using the service
            updated_config = config_service.save_config(config, request.user.id)
            
            return Response(SystemConfigSerializer(updated_config._model).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def batch_update(self, request):
        """Update multiple configurations at once."""
        configs = {}
        
        # Extract config values from form data
        for key, value in request.data.items():
            if key.startswith('value_'):
                config_key = key[6:]  # Remove 'value_' prefix
                configs[config_key] = value
        
        # Update the configs
        results = config_service.update_multiple_configs(configs, request.user.id)
        
        return Response({
            'success': True,
            'updated': results
        })
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export all configurations as JSON."""
        configs = config_service.get_all_configs()
        
        # Convert to serializable dict
        export_data = []
        for config in configs:
            export_data.append({
                'key': config.key,
                'value': config.value,
                'category': config.category,
                'description': config.description,
                'data_type': config.data_type
            })
        
        # Create a JSON response
        response = HttpResponse(
            json.dumps(export_data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="cbs_config_export.json"'
        return response
    
    @action(detail=False, methods=['post'])
    def import_config(self, request):
        """Import configurations from JSON file."""
        try:
            config_file = request.FILES.get('config_file')
            
            if not config_file:
                return Response(
                    {'error': 'No configuration file provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse the JSON file
            import_data = json.loads(config_file.read())
            
            # Process each config
            results = {}
            for item in import_data:
                key = item.get('key')
                if not key:
                    continue
                
                # Check if config exists
                existing_config = config_service.get_config_by_key(key)
                
                if existing_config:
                    # Update existing config
                    existing_config.value = item.get('value', existing_config.value)
                    existing_config.category = item.get('category', existing_config.category)
                    existing_config.description = item.get('description', existing_config.description)
                    existing_config.data_type = item.get('data_type', existing_config.data_type)
                    
                    config_service.save_config(existing_config, request.user.id)
                    results[key] = 'updated'
                else:
                    # Create new config
                    new_config = SystemConfig(
                        key=key,
                        value=item.get('value'),
                        category=item.get('category', 'Imported'),
                        description=item.get('description', ''),
                        data_type=item.get('data_type', 'STRING')
                    )
                    
                    config_service.save_config(new_config, request.user.id)
                    results[key] = 'created'
            
            return Response({
                'success': True,
                'results': results,
                'imported': len(results)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error importing configuration: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def get_queryset(self):
        """
        Optionally restricts the returned configs to a given module or category,
        by filtering against query parameters in the URL.
        """
        queryset = SystemConfig.objects.all()
        module_id = self.request.query_params.get('module', None)
        category = self.request.query_params.get('category', None)
        
        if module_id is not None:
            queryset = queryset.filter(module__id=module_id)
        
        if category is not None:
            queryset = queryset.filter(category=category)
        
        return queryset


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for audit logs (read-only)."""
    queryset = AuditLog.objects.all().order_by('-timestamp')
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """
        Filter audit logs based on query parameters.
        """
        queryset = AuditLog.objects.all().order_by('-timestamp')
        user_id = self.request.query_params.get('user', None)
        resource_type = self.request.query_params.get('resource_type', None)
        resource_id = self.request.query_params.get('resource_id', None)
        action = self.request.query_params.get('action', None)
        severity = self.request.query_params.get('severity', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if user_id is not None:
            queryset = queryset.filter(user__id=user_id)
        
        if resource_type is not None:
            queryset = queryset.filter(resource_type=resource_type)
        
        if resource_id is not None:
            queryset = queryset.filter(resource_id=resource_id)
        
        if action is not None:
            queryset = queryset.filter(action=action)
        
        if severity is not None:
            queryset = queryset.filter(severity=severity)
        
        if start_date is not None and end_date is not None:
            queryset = queryset.filter(timestamp__range=[start_date, end_date])
        
        return queryset


class SystemHealthViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for system health metrics (read-only)."""
    queryset = SystemHealth.objects.all().order_by('-timestamp')
    serializer_class = SystemHealthSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get a summary of system health."""
        system_health = monitoring_service.get_system_health()
        
        if not system_health:
            return Response(
                {'error': 'No health data available'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get module health data
        module_health = monitoring_service.check_all_modules_health()
        
        # Prepare response data
        response_data = {
            'system': {
                'status': system_health.status,
                'cpu_usage': system_health.cpu_usage,
                'memory_usage': system_health.memory_usage,
                'disk_usage': system_health.disk_usage,
                'average_response_time': system_health.average_response_time,
                'timestamp': system_health.timestamp.isoformat(),
            },
            'modules': module_health
        }
        
        return Response(response_data)
    
    @action(detail=False, methods=['get'])
    def report(self, request):
        """Generate a performance report."""
        report = monitoring_service.generate_performance_report()
        return Response(report)
    
    @action(detail=True, methods=['post'])
    def check_module(self, request, pk=None):
        """Perform a health check on a specific module."""
        module_id = pk
        
        # Get current module health
        module_health = monitoring_service.get_module_health(module_id)
        
        if not module_health:
            return Response(
                {'error': f'No health data available for module {module_id}'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(module_health)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get health history for charting."""
        days = request.query_params.get('days', 7)
        try:
            days = int(days)
        except ValueError:
            days = 7
        
        history = monitoring_service.get_health_history(days)
        
        # Format for response
        data = []
        for item in history:
            data.append({
                'timestamp': item.timestamp.isoformat(),
                'status': item.status,
                'cpu_usage': item.cpu_usage,
                'memory_usage': item.memory_usage,
                'disk_usage': item.disk_usage,
                'average_response_time': item.average_response_time
            })
        
        return Response(data)
    
    def get_queryset(self):
        """
        Filter health metrics based on query parameters.
        """
        queryset = SystemHealth.objects.all().order_by('-timestamp')
        component = self.request.query_params.get('component', None)
        status = self.request.query_params.get('status', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if component is not None:
            queryset = queryset.filter(component=component)
        
        if status is not None:
            queryset = queryset.filter(status=status)
        
        if start_date is not None and end_date is not None:
            queryset = queryset.filter(timestamp__range=[start_date, end_date])
        
        return queryset
