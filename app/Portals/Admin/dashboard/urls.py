"""
Admin Dashboard URL Configuration
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='admin_dashboard'),
    path('modules/', views.module_management, name='module_management'),
    path('modules/<str:module_id>/', views.module_detail, name='module_detail'),
    path('modules/<str:module_id>/toggle/', views.toggle_module, name='toggle_module'),
    path('modules/<str:module_id>/features/<str:feature_name>/toggle/', views.toggle_feature, name='toggle_feature'),
    path('api/', views.api_management, name='api_management'),
    path('api/endpoints/<str:endpoint_id>/toggle/', views.toggle_endpoint, name='toggle_endpoint'),
    path('system/health/', views.system_health, name='system_health'),
]
