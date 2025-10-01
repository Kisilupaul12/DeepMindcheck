from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    """Extended user profile for additional information"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # Privacy settings
    allow_data_collection = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=False)
    
    # Statistics
    total_analyses = models.PositiveIntegerField(default=0)
    joined_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"