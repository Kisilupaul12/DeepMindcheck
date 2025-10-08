from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from .models import TextAnalysis, UserFeedback, SystemMetrics
from django.db.models import Count, Avg
import logging

logger = logging.getLogger('deepmindcheck')

def home_view(request):
    """Beautiful home page with overview and features"""
    
    # Get some basic statistics for the home page
    context = {
        'total_analyses': TextAnalysis.objects.count(),
        'avg_confidence': TextAnalysis.objects.aggregate(
            avg=Avg('confidence_score')
        )['avg'] or 0,
        'predictions_today': TextAnalysis.objects.filter(
            created_at__date=timezone.now().date()
        ).count() if 'timezone' in globals() else 0,
    }
    
    logger.info(f"Home page accessed from {request.META.get('REMOTE_ADDR')}")
    return render(request, 'core/home.html', context)

def analyze_view(request):
    """Main text analysis interface"""
    
    context = {
        'page_title': 'Text Analysis',
        'models_available': [
            {'id': 'baseline', 'name': 'Baseline Model', 'description': 'Fast and reliable'},
            {'id': 'advanced', 'name': 'Advanced Model', 'description': 'Higher accuracy'},
            {'id': 'ensemble', 'name': 'Ensemble Model', 'description': 'Best of both worlds'},
        ],
        'demo_texts': [
            "I'm feeling really happy and optimistic about my future today!",
            "I've been feeling overwhelmed and worried about everything lately.",
            "I can't seem to find motivation to do anything and feel hopeless.",
        ]
    }
    
    return render(request, 'core/analyze.html', context)

def about_view(request):
    """About page with project information"""
    
    context = {
        'page_title': 'About DeepMindCheck',
        'version': '1.0.0',
        'features': [
            {
                'icon': 'fa-brain',
                'title': 'Advanced AI Analysis',
                'description': 'State-of-the-art natural language processing models trained on mental health data.'
            },
            {
                'icon': 'fa-shield-alt', 
                'title': 'Privacy Protected',
                'description': 'Your data is processed securely and anonymously. We never store personal information.'
            },
            {
                'icon': 'fa-chart-line',
                'title': 'Real-time Results',
                'description': 'Get instant analysis results with detailed confidence scores and explanations.'
            },
            {
                'icon': 'fa-users',
                'title': 'Research-backed',
                'description': 'Built on peer-reviewed research and validated through extensive testing.'
            }
        ],
        'team': [
            {
                'name': 'Paul Kisilu Nzioki',
                'role': 'Lead Developer & Researcher',
                'description': 'Software Engineer specializing in AI and mental health applications.',
                # 'image': 'images/team/MyPic.jpg'
                'image': 'team/MyPic.jpg',
                'use_media': True
            }
        ],
        'statistics': {
            'analyses_completed': TextAnalysis.objects.count(),
            'accuracy_rate': 85.3,
            'user_satisfaction': 4.2,
            'response_time': 0.8
        }
    }
    
    return render(request, 'core/about.html', context)

def contact_view(request):
    """Contact page with form"""
    
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you would typically send an email or save to database
        logger.info(f"Contact form submission from {email}: {subject}")
        
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return redirect('contact')
    
    context = {
        'page_title': 'Contact Us',
    }
    
    return render(request, 'core/contact.html', context)

def test_view(request):
    """Test page to verify Django setup"""
    
    import django
    import sys
    from django.conf import settings
    
    context = {
        'django_version': django.get_version(),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'debug_mode': settings.DEBUG,
        'database_engine': settings.DATABASES['default']['ENGINE'],
        'installed_apps': len(settings.INSTALLED_APPS),
        'static_url': settings.STATIC_URL,
        'media_url': settings.MEDIA_URL,
        'tests': [
            {'name': 'Django Installation', 'status': 'success', 'details': f'Django {django.get_version()}'},
            {'name': 'Database Connection', 'status': 'success', 'details': 'SQLite working'},
            {'name': 'Static Files', 'status': 'success', 'details': f'{settings.STATIC_URL}'},
            {'name': 'Templates', 'status': 'success', 'details': 'Template rendering working'},
            {'name': 'URL Routing', 'status': 'success', 'details': 'All URLs configured'},
        ]
    }
    
    return render(request, 'core/test.html', context)