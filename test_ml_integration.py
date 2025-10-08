"""
Test ML Integration
Run this to verify everything works
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deepmindcheck.settings')
django.setup()

from ml_models import get_predictor

def test_predictor():
    """Test the ML predictor"""
    
    print("="*60)
    print("Testing DeepMindCheck ML Integration")
    print("="*60)
    
    # Test 1: Load model
    print("\n1. Loading models...")
    try:
        predictor = get_predictor()
        print(f"   ✅ Models loaded successfully!")
        print(f"   Model: {predictor.deployment_info.get('model_name')}")
    except Exception as e:
        print(f"   ❌ Failed to load models: {e}")
        return
    
    # Test 2: Model info
    print("\n2. Getting model info...")
    info = predictor.get_model_info()
    print(f"   Status: {info['status']}")
    print(f"   Classes: {info['classes']}")
    if 'performance' in info:
        print(f"   F1 Score: {info['performance'].get('f1_score', 0):.3f}")
    
    # Test 3: Test predictions
    print("\n3. Testing predictions...")
    test_texts = [
        "I'm feeling really happy and optimistic about life!",
        "I feel so sad and hopeless, can't find any motivation",
        "I'm constantly worried and anxious about everything"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n   Test {i}: \"{text[:50]}...\"")
        try:
            result = predictor.predict(text)
            print(f"   Prediction: {result['prediction']}")
            print(f"   Confidence: {result['confidence']:.3f}")
            print(f"   Probabilities: {result['probabilities']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "="*60)
    print("Testing complete!")
    print("="*60)

if __name__ == '__main__':
    test_predictor()