from django.db import models
from django.contrib.auth.models import User


class Analysis(models.Model):
    """Represents a text analysis result."""
    PREDICTION_CHOICES = [
        ("positive", "Positive"),
        ("negative", "Negative"),
        ("neutral", "Neutral"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="analyses"
    )
    input_text = models.TextField(help_text="Original text submitted")
    prediction = models.CharField(
        max_length=50, choices=PREDICTION_CHOICES, default="other"
    )
    confidence = models.FloatField(help_text="Confidence score", null=True, blank=True)
    model_used = models.CharField(max_length=100, help_text="Model name")
    response_time = models.FloatField(help_text="Processing time (seconds)", null=True, blank=True)
    text_length = models.IntegerField(help_text="Length of input text", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis {self.id} - {self.prediction}"


class Feedback(models.Model):
    """Stores user feedback on an analysis."""
    analysis = models.ForeignKey(
        Analysis, on_delete=models.CASCADE, related_name="feedbacks"
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="feedbacks"
    )
    rating = models.IntegerField(
        choices=[(1, "Very Poor"), (2, "Poor"), (3, "Average"), (4, "Good"), (5, "Excellent")],
        default=3
    )
    feedback_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback {self.id} - Rating {self.rating}"
