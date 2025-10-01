"""
URL configuration for DeepMindCheck project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('analytics/', include('analytics.urls')),
    path('accounts/', include('accounts.urls')),
    path('', include('core.urls')),
    
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "DeepMindCheck Administration"
admin.site.site_title = "DeepMindCheck Admin Portal"
admin.site.index_title = "Welcome to DeepMindCheck Administration"