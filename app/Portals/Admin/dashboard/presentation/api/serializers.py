"""
Serializers for the admin dashboard API.
"""
from rest_framework import serializers
from dashboard.models import Module, ApiEndpoint, AdminUser, SystemConfig, AuditLog, SystemHealth, FeatureFlag


class FeatureFlagSerializer(serializers.ModelSerializer):
    """Serializer for feature flags."""
    
    class Meta:
        model = FeatureFlag
        fields = ['id', 'name', 'description', 'enabled', 'affects_endpoints', 'created_at', 'updated_at']


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer for modules."""
    features = FeatureFlagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Module
        fields = ['id', 'name', 'version', 'status', 'description', 'dependencies', 'features', 'last_modified']


class ApiEndpointSerializer(serializers.ModelSerializer):
    """Serializer for API endpoints."""
    module_name = serializers.CharField(source='module.name', read_only=True)
    
    class Meta:
        model = ApiEndpoint
        fields = ['id', 'path', 'module', 'module_name', 'method', 'enabled', 'auth_required', 
                  'rate_limit', 'description', 'last_accessed', 'success_count', 'error_count', 
                  'created_at', 'updated_at']


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin users."""
    
    class Meta:
        model = AdminUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'mfa_enabled', 
                  'is_active', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class SystemConfigSerializer(serializers.ModelSerializer):
    """Serializer for system configuration."""
    module_name = serializers.CharField(source='module.name', read_only=True)
    modified_by_username = serializers.CharField(source='modified_by.username', read_only=True)
    
    class Meta:
        model = SystemConfig
        fields = ['id', 'key', 'value', 'type', 'module', 'module_name', 'description', 
                  'is_sensitive', 'allowed_values', 'last_modified', 'modified_by', 'modified_by_username']


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs."""
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'timestamp', 'user', 'user_username', 'action', 'resource_type', 'resource_id', 
                  'severity', 'details', 'ip_address', 'success', 'error_message']


class SystemHealthSerializer(serializers.ModelSerializer):
    """Serializer for system health metrics."""
    
    class Meta:
        model = SystemHealth
        fields = ['id', 'component', 'status', 'timestamp', 'metrics', 'details', 'alerts']


# Request and response serializers for specific API endpoints
class ModuleToggleRequestSerializer(serializers.Serializer):
    """Request serializer for toggling a module."""
    enabled = serializers.BooleanField(required=True)


class ApiEndpointToggleRequestSerializer(serializers.Serializer):
    """Request serializer for toggling an API endpoint."""
    enabled = serializers.BooleanField(required=True)


class RateLimitRequestSerializer(serializers.Serializer):
    """Request serializer for setting a rate limit."""
    rate_limit = serializers.IntegerField(required=True, min_value=0)


class ConfigUpdateRequestSerializer(serializers.Serializer):
    """Request serializer for updating configuration."""
    value = serializers.JSONField(required=True)


class LoginRequestSerializer(serializers.Serializer):
    """Request serializer for login."""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, style={'input_type': 'password'})


class LoginResponseSerializer(serializers.Serializer):
    """Response serializer for login."""
    token = serializers.CharField()
    user = AdminUserSerializer()


class PasswordChangeRequestSerializer(serializers.Serializer):
    """Request serializer for password change."""
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate(self, data):
        """Validate that new_password and confirm_password match."""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New password and confirm password do not match.")
        return data
