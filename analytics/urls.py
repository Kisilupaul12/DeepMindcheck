from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='analytics_dashboard'),
    path('reports/', views.reports_view, name='analytics_reports'),
    path('export/', views.export_data, name='analytics_export'),
]