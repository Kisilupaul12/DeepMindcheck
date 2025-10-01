from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'total_analyses', 'joined_date')
    list_filter = ('allow_data_collection', 'email_notifications', 'joined_date')
    search_fields = ('user__username', 'user__email', 'location')
    readonly_fields = ('joined_date',)