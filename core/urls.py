from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('analyze/', views.analyze_view, name='analyze'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('test/', views.test_view, name='test'),
]