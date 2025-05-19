"""
URL configuration for the admin dashboard web views.
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from dashboard.presentation.views.dashboard_views import (
    dashboard_home, module_list, module_detail, toggle_module,
    endpoint_list, toggle_endpoint, audit_logs, system_health,
    system_config, login_view, logout_view
)

urlpatterns = [
    # Dashboard home
    path('', dashboard_home, name='dashboard_home'),
    
    # Module management
    path('modules/', module_list, name='module_list'),
    path('modules/<str:module_id>/', module_detail, name='module_detail'),
    path('modules/<str:module_id>/toggle/', toggle_module, name='toggle_module'),
    
    # API endpoint management
    path('endpoints/', endpoint_list, name='endpoint_list'),
    path('endpoints/<str:endpoint_id>/toggle/', toggle_endpoint, name='toggle_endpoint'),
    
    # Audit logs
    path('audit/logs/', audit_logs, name='audit_logs'),
    
    # System health
    path('monitoring/health/', system_health, name='system_health'),
    
    # System configuration
    path('config/', system_config, name='system_config'),
    
    # Authentication
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]
