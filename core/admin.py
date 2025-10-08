from django.contrib import admin
from .models import TextAnalysis, UserFeedback, SystemMetrics

@admin.register(TextAnalysis)
class TextAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'prediction', 'confidence_percentage', 'model_used', 'created_at', 'has_feedback')
    list_filter = ('prediction', 'model_used', 'created_at')
    search_fields = ('text_input', 'session_id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    def has_feedback(self, obj):
        return hasattr(obj, 'feedback')
    has_feedback.boolean = True
    has_feedback.short_description = 'Has Feedback'

@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'analysis', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('feedback_text',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_analyses', 'feedback_count', 'average_rating', 'feedback_rate')
    list_filter = ('date',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'