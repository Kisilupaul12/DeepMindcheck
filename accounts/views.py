from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import models
from .models import UserProfile

def login_view(request):
    """User login view"""
    
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect to next page or home
            next_page = request.GET.get('next', 'home')
            return redirect(next_page)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    context = {
        'form': form,
        'page_title': 'Login'
    }
    
    return render(request, 'accounts/login.html', context)

def register_view(request):
    """User registration view"""
    
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Log in the user
            login(request, user)
            messages.success(request, f'Welcome to DeepMindCheck, {user.username}!')
            
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
    
    context = {
        'form': form,
        'page_title': 'Register'
    }
    
    return render(request, 'accounts/register.html', context)

def logout_view(request):
    """User logout view"""
    
    if request.user.is_authenticated:
        messages.success(request, f'Goodbye, {request.user.username}!')
        logout(request)
    
    return redirect('home')

@login_required
def profile_view(request):
    """User profile view"""
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user's analysis statistics
    from core.models import TextAnalysis, UserFeedback
    
    user_analyses = TextAnalysis.objects.filter(user=request.user)
    user_stats = {
        'total_analyses': user_analyses.count(),
        'avg_confidence': user_analyses.aggregate(avg=models.Avg('confidence_score'))['avg'] or 0,
        'feedback_given': UserFeedback.objects.filter(analysis__user=request.user).count(),
    }
    
    # Recent analyses
    recent_analyses = user_analyses.order_by('-created_at')[:5]
    
    context = {
        'profile': profile,
        'user_stats': user_stats,
        'recent_analyses': recent_analyses,
        'page_title': f'{request.user.username} Profile'
    }
    
    return render(request, 'accounts/profile.html', context)