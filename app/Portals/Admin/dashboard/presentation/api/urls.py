"""
URL configuration for the admin dashboard API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from dashboard.presentation.api.views import (
    ModuleViewSet, ApiEndpointViewSet, AdminUserViewSet, 
    SystemConfigViewSet, AuditLogViewSet, SystemHealthViewSet,
    LoginView, PasswordChangeView
)
from dashboard.presentation.api.module_endpoints import (
    ModuleRegistrationView, ApiEndpointRegistrationView,
    FeatureFlagRegistrationView, ConfigurationRegistrationView,
    HealthMetricsRegistrationView
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'modules', ModuleViewSet)
router.register(r'endpoints', ApiEndpointViewSet)
router.register(r'users', AdminUserViewSet)
router.register(r'configs', SystemConfigViewSet)
router.register(r'logs', AuditLogViewSet)
router.register(r'health', SystemHealthViewSet)

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/change-password/', PasswordChangeView.as_view(), name='change-password'),
    
    # Module registration endpoints
    path('modules/register/', ModuleRegistrationView.as_view(), name='module-registration'),
    path('api/endpoints/register/', ApiEndpointRegistrationView.as_view(), name='api-endpoint-registration'),
    path('features/register/', FeatureFlagRegistrationView.as_view(), name='feature-flag-registration'),
    path('configs/register/', ConfigurationRegistrationView.as_view(), name='configuration-registration'),
    path('health/metrics/', HealthMetricsRegistrationView.as_view(), name='health-metrics-registration'),
]
