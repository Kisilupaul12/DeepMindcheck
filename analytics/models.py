# analytics/models.py
# This app doesn't need its own models - it uses core.models
# Remove any existing models and add this:

from core.models import TextAnalysis, UserFeedback, SystemMetrics

# Re-export for convenience
__all__ = ['TextAnalysis', 'UserFeedback', 'SystemMetrics']