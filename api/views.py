"""
Updated API Views - Real ML Model Integration
Replace your existing api/views.py with this
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.models import TextAnalysis, UserFeedback, SystemMetrics
from django.db.models import Count, Avg, Q
from django.utils import timezone
import json
import time
import logging

# Import our ML predictor
from ml_models import get_predictor

logger = logging.getLogger('deepmindcheck')

@api_view(['POST'])
@permission_classes([AllowAny])
def analyze_text(request):
    """
    Real ML-powered text analysis endpoint
    """
    try:
        # Get request data
        text = request.data.get('text', '').strip()
        model_choice = request.data.get('model', 'baseline')
        include_explanation = request.data.get('explain', False)
        
        # Validation
        if not text:
            return Response({
                'error': 'Text input is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(text) < 10:
            return Response({
                'error': 'Text must be at least 10 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(text) > 2000:
            return Response({
                'error': 'Text must be less than 2000 characters'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Start timing
        start_time = time.time()
        
        # Get predictor and make prediction
        try:
            predictor = get_predictor()
            
            # Make prediction using real ML model
            ml_result = predictor.predict(text, include_probabilities=True)
            
            prediction = ml_result['prediction']
            confidence = ml_result['confidence']
            probabilities = ml_result['probabilities']
            model_used = ml_result['model_name']
            
            logger.info(f"ML Prediction: {prediction} ({confidence:.3f})")
            
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return Response({
                'error': f'Analysis failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        processing_time = time.time() - start_time
        
        # Create analysis record
        analysis = TextAnalysis.objects.create(
            text_input=text,
            text_length=len(text),
            prediction=prediction,
            confidence_score=confidence,
            probabilities=probabilities,
            model_used=model_choice,
            processing_time=processing_time,
            session_id=request.session.session_key or str(uuid.uuid4())[:8],
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Generate response
        response_data = {
            'id': str(analysis.id),
            'prediction': prediction,
            'confidence': confidence,
            'probabilities': probabilities,
            'model_used': model_used,
            'processing_time': round(processing_time, 3),
            'text_length': len(text),
            'message': generate_message(prediction, confidence),
            'recommendations': generate_recommendations(prediction),
        }
        
        # Add explanation if requested
        if include_explanation:
            response_data['explanation'] = generate_explanation(prediction, confidence, text)
        
        logger.info(f"Analysis completed: {prediction} ({confidence:.3f}) - {len(text)} chars")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return Response({
            'error': 'Analysis failed. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_feedback(request):
    """Submit user feedback for an analysis"""
    try:
        analysis_id = request.data.get('analysis_id')
        rating = request.data.get('rating')
        feedback_text = request.data.get('feedback_text', '')
        is_helpful = request.data.get('is_helpful')
        
        # Validation
        if not analysis_id:
            return Response({'error': 'Analysis ID required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not rating or rating not in [1, 2, 3, 4, 5]:
            return Response({'error': 'Rating must be 1-5'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get analysis
        try:
            analysis = TextAnalysis.objects.get(id=analysis_id)
        except TextAnalysis.DoesNotExist:
            return Response({'error': 'Analysis not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if feedback already exists
        if hasattr(analysis, 'feedback'):
            return Response({'error': 'Feedback already submitted'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create feedback
        feedback = UserFeedback.objects.create(
            analysis=analysis,
            rating=rating,
            feedback_text=feedback_text,
            is_helpful=is_helpful
        )
        
        logger.info(f"Feedback submitted: {rating}/5 for analysis {analysis_id}")
        
        return Response({
            'success': True,
            'message': 'Thank you for your feedback!',
            'feedback_id': feedback.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Feedback error: {str(e)}")
        return Response({
            'error': 'Failed to submit feedback'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def analytics_dashboard_data(request):
    """Get analytics data for dashboard"""
    try:
        # Overall statistics
        total_analyses = TextAnalysis.objects.count()
        
        # Prediction distribution
        prediction_dist = TextAnalysis.objects.values('prediction').annotate(
            count=Count('prediction')
        ).order_by('-count')
        
        # Model performance
        model_stats = TextAnalysis.objects.values('model_used').annotate(
            count=Count('model_used'),
            avg_confidence=Avg('confidence_score'),
            avg_time=Avg('processing_time')
        )
        
        # Feedback statistics
        feedback_count = UserFeedback.objects.count()
        avg_rating = UserFeedback.objects.aggregate(Avg('rating'))['rating__avg'] or 0
        
        # Recent activity (last 7 days)
        week_ago = timezone.now() - timezone.timedelta(days=7)
        daily_counts = []
        for i in range(7):
            date = (timezone.now() - timezone.timedelta(days=i)).date()
            count = TextAnalysis.objects.filter(created_at__date=date).count()
            daily_counts.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        daily_counts.reverse()
        
        data = {
            'total_analyses': total_analyses,
            'feedback_count': feedback_count,
            'average_rating': round(avg_rating, 2),
            'feedback_rate': round((feedback_count / max(total_analyses, 1)) * 100, 1),
            'prediction_distribution': list(prediction_dist),
            'model_statistics': list(model_stats),
            'daily_activity': daily_counts
        }
        
        return Response(data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        return Response({
            'error': 'Failed to fetch analytics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def model_info(request):
    """Get information about the loaded ML model"""
    try:
        predictor = get_predictor()
        info = predictor.get_model_info()
        
        return Response(info, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Model info error: {str(e)}")
        return Response({
            'error': 'Failed to get model information',
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """API health check endpoint"""
    try:
        # Check if ML model is loaded
        predictor = get_predictor()
        model_loaded = predictor.is_loaded
        
        # Check database
        db_healthy = TextAnalysis.objects.count() >= 0
        
        health_data = {
            'status': 'healthy' if (model_loaded and db_healthy) else 'degraded',
            'timestamp': timezone.now().isoformat(),
            'components': {
                'ml_model': 'loaded' if model_loaded else 'not_loaded',
                'database': 'connected' if db_healthy else 'error'
            }
        }
        
        status_code = status.HTTP_200_OK if health_data['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_data, status=status_code)
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return Response({
            'status': 'unhealthy',
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# Helper Functions

import uuid

def generate_message(prediction, confidence):
    """Generate contextual message based on prediction"""
    
    messages = {
        'neutral': {
            'high': "Your text suggests a balanced and positive mental state. Keep maintaining good mental health practices!",
            'medium': "Your text appears mostly neutral. Continue focusing on your well-being.",
            'low': "The analysis suggests a generally stable state, though some patterns are unclear."
        },
        'depression': {
            'high': "Your text shows patterns that may indicate depressive thoughts. Please consider reaching out to a mental health professional or trusted person.",
            'medium': "Some concerning patterns detected in your text. It might be helpful to talk to someone you trust.",
            'low': "Your text contains some indicators that warrant attention. Consider monitoring your mental health."
        },
        'anxiety': {
            'high': "Your text suggests elevated stress or anxiety levels. Relaxation techniques and professional support may be beneficial.",
            'medium': "Some stress or anxiety indicators detected. Consider practicing stress management techniques.",
            'low': "Mild stress patterns observed. Regular self-care practices may be helpful."
        }
    }
    
    level = 'high' if confidence > 0.7 else 'medium' if confidence > 0.5 else 'low'
    return messages.get(prediction, {}).get(level, "Analysis complete.")


def generate_recommendations(prediction):
    """Generate helpful recommendations based on prediction"""
    
    recommendations = {
        'neutral': [
            "Continue healthy lifestyle habits and regular exercise",
            "Maintain strong social connections with friends and family",
            "Practice mindfulness or meditation regularly",
            "Keep a gratitude journal to maintain positive outlook"
        ],
        'depression': [
            "Consider speaking with a mental health professional",
            "Reach out to trusted friends, family members, or support groups", 
            "Maintain physical activity and spend time in natural light",
            "Establish a regular sleep schedule and healthy routine",
            "Avoid isolation - stay connected with supportive people"
        ],
        'anxiety': [
            "Practice deep breathing exercises and progressive muscle relaxation",
            "Try mindfulness meditation or grounding techniques",
            "Consider limiting caffeine intake and maintaining regular sleep",
            "Engage in regular physical exercise to reduce stress",
            "Talk to a counselor or therapist about anxiety management"
        ]
    }
    
    return recommendations.get(prediction, [])


def generate_explanation(prediction, confidence, text):
    """Generate explanation for the prediction"""
    
    explanations = {
        'depression': "The model detected language patterns and word choices commonly associated with depressive thoughts, including expressions of hopelessness, sadness, or negative self-perception.",
        'anxiety': "The analysis identified linguistic markers typically associated with anxiety, such as expressions of worry, nervousness, or stress-related concerns.",
        'neutral': "The language patterns in your text appear balanced and don't strongly indicate specific mental health concerns, suggesting a relatively stable emotional state."
    }
    
    confidence_explanation = f"The model's confidence in this prediction is {confidence:.1%}. "
    
    if confidence > 0.8:
        confidence_explanation += "This indicates a strong pattern match with the training data."
    elif confidence > 0.6:
        confidence_explanation += "This suggests a moderate pattern match with some uncertainty."
    else:
        confidence_explanation += "This indicates lower certainty, suggesting mixed or unclear patterns."
    
    return {
        'reasoning': explanations.get(prediction, "Analysis complete."),
        'confidence_explanation': confidence_explanation,
        'model_details': f"Using gradient boosting model with character-level TF-IDF features.",
        'disclaimer': 'This analysis is for informational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment.'
    }


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip