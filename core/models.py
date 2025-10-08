from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class TextAnalysis(models.Model):
    """Model to store text analysis results"""
    
    PREDICTION_CHOICES = [
        ('neutral', 'Neutral'),
        ('depression', 'Depression'),  
        ('anxiety', 'Anxiety'),
        
    ]
    
    MODEL_CHOICES = [
        ('baseline', 'Baseline Model'),
        ('advanced', 'Advanced Model'),
        ('ensemble', 'Ensemble Model'),
    ]
    
    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User information (optional)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, help_text="Anonymous session tracking")
    
    # Input data
    text_input = models.TextField(help_text="Original text submitted for analysis")
    text_length = models.PositiveIntegerField()
    
    # Analysis results
    prediction = models.CharField(max_length=20, choices=PREDICTION_CHOICES)
    confidence_score = models.FloatField(help_text="Model confidence (0-1)")
    probabilities = models.JSONField(help_text="All class probabilities")
    
    # Model information
    model_used = models.CharField(max_length=20, choices=MODEL_CHOICES, default='baseline')
    model_version = models.CharField(max_length=10, default='1.0')
    
    # Performance metrics
    processing_time = models.FloatField(help_text="Time taken to process (seconds)")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['prediction', 'created_at']),
            models.Index(fields=['model_used', 'created_at']),
            models.Index(fields=['session_id']),
        ]
    
    def __str__(self):
        return f"{self.prediction} - {self.confidence_score:.2f} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def confidence_percentage(self):
        return round(self.confidence_score * 100, 1)

class UserFeedback(models.Model):
    """Model to store user feedback on predictions"""
    
    RATING_CHOICES = [
        (1, '⭐ Poor'),
        (2, '⭐⭐ Fair'), 
        (3, '⭐⭐⭐ Good'),
        (4, '⭐⭐⭐⭐ Very Good'),
        (5, '⭐⭐⭐⭐⭐ Excellent'),
    ]
    
    analysis = models.OneToOneField(TextAnalysis, on_delete=models.CASCADE, related_name='feedback')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    feedback_text = models.TextField(blank=True, help_text="Optional written feedback")
    is_helpful = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Rating: {self.rating}/5 for {self.analysis.prediction}"

class SystemMetrics(models.Model):
    """Model to store daily system metrics"""
    
    date = models.DateField(unique=True, default=timezone.now)
    total_analyses = models.PositiveIntegerField(default=0)
    unique_sessions = models.PositiveIntegerField(default=0)
    average_confidence = models.FloatField(default=0.0)
    average_processing_time = models.FloatField(default=0.0)
    feedback_count = models.PositiveIntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    
    # Prediction distribution
    neutral_count = models.PositiveIntegerField(default=0)
    depression_count = models.PositiveIntegerField(default=0)
    anxiety_count = models.PositiveIntegerField(default=0)
    stress_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"Metrics for {self.date}"
    
    @property
    def total_predictions_with_feedback(self):
        return self.feedback_count
    
    @property
    def feedback_rate(self):
        if self.total_analyses > 0:
            return round((self.feedback_count / self.total_analyses) * 100, 1)
        return 0