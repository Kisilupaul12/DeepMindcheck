from django.urls import path
from . import views

urlpatterns = [
    path('analyze/', views.analyze_text, name='api_analyze'),
    path('feedback/', views.submit_feedback, name='api_feedback'),
    path('analytics/dashboard/', views.analytics_dashboard_data, name='api_analytics'),
    path('model-info/', views.model_info, name='api_model_info'),
    path('health/', views.health_check, name='api_health'),
]