from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from core.models import TextAnalysis, UserFeedback, SystemMetrics
from django.db.models import Count, Avg, Q
from django.utils import timezone
import json
import time
import random
import uuid
import logging

logger = logging.getLogger('deepmindcheck')

@api_view(['POST'])
@permission_classes([AllowAny])
def analyze_text(request):
    """
    Advanced text analysis endpoint with demo functionality
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
        
        # Simulate processing time
        start_time = time.time()
        time.sleep(random.uniform(0.3, 0.8))  # Realistic processing delay
        
        # Demo prediction logic (replace with real model)
        prediction, confidence, probabilities = generate_demo_prediction(text)
        
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
            'model_used': model_choice,
            'processing_time': round(processing_time, 3),
            'text_length': len(text),
            'message': generate_message(prediction, confidence),
            'recommendations': generate_recommendations(prediction),
        }
        
        # Add explanation if requested
        if include_explanation:
            response_data['explanation'] = generate_explanation(prediction, confidence, text)
        
        logger.info(f"Text analysis completed: {prediction} ({confidence:.3f}) - {len(text)} chars")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return Response({
            'error': 'Analysis failed. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def generate_demo_prediction(text):
    """Generate realistic demo predictions based on text content"""
    
    text_lower = text.lower()
    
    # Keywords for different mental health states
    depression_keywords = ['sad', 'depressed', 'hopeless', 'worthless', 'tired', 'empty', 'lonely', 'useless']
    anxiety_keywords = ['anxious', 'worried', 'nervous', 'panic', 'stress', 'overwhelmed', 'scared', 'fear']
    neutral_keywords = ['happy', 'good', 'great', 'excited', 'positive', 'love', 'joy', 'wonderful']
    
    # Count keyword matches
    depression_score = sum(1 for word in depression_keywords if word in text_lower)
    anxiety_score = sum(1 for word in anxiety_keywords if word in text_lower)
    neutral_score = sum(1 for word in neutral_keywords if word in text_lower)
    
    # Determine prediction based on scores
    if depression_score > anxiety_score and depression_score > neutral_score:
        prediction = 'depression'
        base_confidence = 0.7 + (depression_score * 0.05)
    elif anxiety_score > depression_score and anxiety_score > neutral_score:
        prediction = 'anxiety'
        base_confidence = 0.7 + (anxiety_score * 0.05)
    elif neutral_score > 0:
        prediction = 'neutral'
        base_confidence = 0.6 + (neutral_score * 0.05)
    else:
        # Default to neutral with lower confidence
        prediction = 'neutral'
        base_confidence = 0.5
    
    # Add some randomness but keep it realistic
    confidence = min(0.95, max(0.3, base_confidence + random.uniform(-0.1, 0.1)))
    
    # Generate probabilities
    probabilities = generate_probabilities(prediction, confidence)
    
    return prediction, confidence, probabilities

def generate_probabilities(prediction, confidence):
    """Generate realistic probability distribution"""
    
    probs = {'neutral': 0.33, 'depression': 0.33, 'anxiety': 0.33}
    probs[prediction] = confidence
    
    remaining = 1.0 - confidence
    other_classes = [k for k in probs.keys() if k != prediction]
    
    for i, other in enumerate(other_classes):
        if i == len(other_classes) - 1:
            probs[other] = remaining
        else:
            prob = random.uniform(0.05, remaining - 0.05)
            probs[other] = prob
            remaining -= prob
    
    return probs

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
    return messages[prediction][level]

def generate_recommendations(prediction):
    """Generate helpful recommendations based on prediction"""
    
    recommendations = {
        'neutral': [
            "Continue healthy lifestyle habits and regular exercise",
            "Maintain strong social connections with friends and family",
            "Practice mindfulness or meditation regularly"
        ],
        'depression': [
            "Consider speaking with a mental health professional",
            "Reach out to trusted friends, family members, or support groups", 
            "Maintain physical activity and spend time in natural light"
        ],
        'anxiety': [
            "Practice deep breathing exercises and progressive muscle relaxation",
            "Try mindfulness meditation or grounding techniques",
            "Consider limiting caffeine intake and maintaining regular sleep"
        ]
    }
    
    return recommendations[prediction]

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
        'reasoning': explanations[prediction],
        'confidence_explanation': confidence_explanation,
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

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_feedback(request):
    """Submit user feedback"""
    try:
        analysis_id = request.data.get('analysis_id')
        rating = request.data.get('rating')
        
        analysis = TextAnalysis.objects.get(id=analysis_id)
        UserFeedback.objects.create(analysis=analysis, rating=rating)
        
        return Response({'message': 'Feedback submitted'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def analytics_dashboard_data(request):
    """Get analytics data"""
    data = {
        'stats': {'total_analyses': TextAnalysis.objects.count()},
        'charts': {}
    }
    return Response(data)

@api_view(['GET'])
@permission_classes([AllowAny])
def model_info(request):
    """Get model information"""
    return Response({
        'available_models': ['baseline', 'advanced', 'ensemble'],
        'default_model': 'baseline'
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """API health check"""
    return Response({'status': 'healthy'})