from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _

class ModuleStatus(models.TextChoices):
    """Status choices for a CBS module."""
    INSTALLED = 'installed', _('Installed')
    ACTIVE = 'active', _('Active')
    DEACTIVATED = 'deactivated', _('Deactivated')
    MAINTENANCE = 'maintenance', _('Maintenance')
    FAILED = 'failed', _('Failed')


class HttpMethod(models.TextChoices):
    """HTTP method choices for API endpoints."""
    GET = 'GET', _('GET')
    POST = 'POST', _('POST')
    PUT = 'PUT', _('PUT')
    PATCH = 'PATCH', _('PATCH')
    DELETE = 'DELETE', _('DELETE')


class AdminRole(models.TextChoices):
    """Role choices for admin users."""
    SUPER_ADMIN = 'super_admin', _('Super Admin')
    SYSTEM_ADMIN = 'system_admin', _('System Admin')
    MODULE_ADMIN = 'module_admin', _('Module Admin')
    API_ADMIN = 'api_admin', _('API Admin')
    AUDIT_ADMIN = 'audit_admin', _('Audit Admin')
    READONLY_ADMIN = 'readonly_admin', _('Read-only Admin')


class ConfigType(models.TextChoices):
    """Type choices for system configuration."""
    SYSTEM = 'system', _('System')
    MODULE = 'module', _('Module')
    API = 'api', _('API')
    FEATURE = 'feature', _('Feature')
    SECURITY = 'security', _('Security')
    PERFORMANCE = 'performance', _('Performance')


class AuditLogAction(models.TextChoices):
    """Action choices for audit logs."""
    CREATE = 'create', _('Create')
    READ = 'read', _('Read')
    UPDATE = 'update', _('Update')
    DELETE = 'delete', _('Delete')
    LOGIN = 'login', _('Login')
    LOGOUT = 'logout', _('Logout')
    ENABLE = 'enable', _('Enable')
    DISABLE = 'disable', _('Disable')
    CONFIGURE = 'configure', _('Configure')
    RESTART = 'restart', _('Restart')


class AuditLogSeverity(models.TextChoices):
    """Severity choices for audit logs."""
    INFO = 'info', _('Info')
    WARNING = 'warning', _('Warning')
    ERROR = 'error', _('Error')
    CRITICAL = 'critical', _('Critical')


class HealthStatus(models.TextChoices):
    """Status choices for system health."""
    HEALTHY = 'healthy', _('Healthy')
    WARNING = 'warning', _('Warning')
    CRITICAL = 'critical', _('Critical')
    UNKNOWN = 'unknown', _('Unknown')


class AdminUser(AbstractUser):
    """Extended Django User model for admin users."""
    role = models.CharField(
        max_length=20,
        choices=AdminRole.choices,
        default=AdminRole.READONLY_ADMIN
    )
    mfa_enabled = models.BooleanField(default=False)
    # For MFA we'd also need additional fields like phone number, etc.
    
    class Meta:
        verbose_name = _('admin user')
        verbose_name_plural = _('admin users')


class Module(models.Model):
    """Model for CBS modules."""
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20,
        choices=ModuleStatus.choices,
        default=ModuleStatus.INSTALLED
    )
    description = models.TextField(blank=True, null=True)
    dependencies = models.JSONField(default=list)  # Store as a list of module IDs
    last_modified = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.version})"


class FeatureFlag(models.Model):
    """Model for feature flags."""
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    enabled = models.BooleanField(default=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='features')
    affects_endpoints = models.JSONField(default=list)  # Store as a list of endpoint IDs
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({'Enabled' if self.enabled else 'Disabled'})"


class ApiEndpoint(models.Model):
    """Model for API endpoints."""
    id = models.CharField(max_length=100, primary_key=True)
    path = models.CharField(max_length=200)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='endpoints')
    method = models.CharField(max_length=10, choices=HttpMethod.choices)
    enabled = models.BooleanField(default=True)
    auth_required = models.BooleanField(default=True)
    rate_limit = models.IntegerField(blank=True, null=True)  # requests per minute
    description = models.TextField(blank=True, null=True)
    last_accessed = models.DateTimeField(blank=True, null=True)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('path', 'method', 'module')
    
    def __str__(self):
        return f"{self.method} {self.path}"


class SystemConfig(models.Model):
    """Model for system configuration."""
    id = models.CharField(max_length=100, primary_key=True)
    key = models.CharField(max_length=100)
    value = models.JSONField()  # Store as JSON to handle different types
    type = models.CharField(max_length=20, choices=ConfigType.choices)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='configs', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_sensitive = models.BooleanField(default=False)
    allowed_values = models.JSONField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, blank=True, null=True)
    
    class Meta:
        unique_together = ('key', 'module')
    
    def __str__(self):
        return f"{self.key} ({self.type})"


class AuditLog(models.Model):
    """Model for audit logs."""
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, blank=True, null=True)
    action = models.CharField(max_length=20, choices=AuditLogAction.choices)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=AuditLogSeverity.choices, default=AuditLogSeverity.INFO)
    details = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def __str__(self):
        return f"{self.timestamp} - {self.action} {self.resource_type}"


class SystemHealth(models.Model):
    """Model for system health metrics."""
    id = models.AutoField(primary_key=True)
    component = models.CharField(max_length=100)  # Module ID or system component name
    status = models.CharField(max_length=20, choices=HealthStatus.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    metrics = models.JSONField(default=dict)
    details = models.JSONField(blank=True, null=True)
    alerts = models.JSONField(default=list)
    
    class Meta:
        indexes = [
            models.Index(fields=['component']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.component} - {self.status} ({self.timestamp})"
