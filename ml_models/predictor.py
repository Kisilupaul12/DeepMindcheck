"""
DeepMindCheck ML Predictor Module
Loads and uses trained mental health classification models
"""

import pickle
import json
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger('deepmindcheck')

class MentalHealthPredictor:
    """
    Production-ready mental health text classifier
    Uses trained gradient boosting model with character-level TF-IDF
    """
    
    def __init__(self, models_dir=None):
        """Initialize predictor and load models"""
        if models_dir is None:
            # Default to ml_models/saved_models in project root
            self.models_dir = Path(__file__).parent / 'saved_models'
        else:
            self.models_dir = Path(models_dir)
        
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.deployment_info = None
        self.is_loaded = False
        
        # Load models on initialization
        self.load_models()
    
    def load_models(self):
        """Load all required models and configuration"""
        try:
            logger.info(f"Loading models from {self.models_dir}")
            
            # Load deployment info
            deployment_path = self.models_dir / 'deployment_info.json'
            if deployment_path.exists():
                with open(deployment_path, 'r') as f:
                    self.deployment_info = json.load(f)
                logger.info(f"Loaded deployment info: {self.deployment_info.get('model_name')}")
            
            # Load model
            model_path = self.models_dir / 'best_model.pkl'
            if not model_path.exists():
                raise FileNotFoundError(f"Model file not found at {model_path}")
            
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            logger.info("Model loaded successfully")
            
            # Load vectorizer
            vectorizer_path = self.models_dir / 'best_vectorizer.pkl'
            if not vectorizer_path.exists():
                raise FileNotFoundError(f"Vectorizer not found at {vectorizer_path}")
            
            with open(vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
            logger.info("Vectorizer loaded successfully")
            
            # Load label encoder
            label_encoder_path = self.models_dir / 'label_encoder.pkl'
            if not label_encoder_path.exists():
                raise FileNotFoundError(f"Label encoder not found at {label_encoder_path}")
            
            with open(label_encoder_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
            logger.info(f"Label encoder loaded. Classes: {self.label_encoder.classes_}")
            
            self.is_loaded = True
            logger.info("All models loaded successfully!")
            
            # Log performance metrics if available
            if self.deployment_info and 'performance' in self.deployment_info:
                perf = self.deployment_info['performance']
                logger.info(f"Model performance - F1: {perf.get('f1_score', 0):.3f}, "
                          f"Accuracy: {perf.get('accuracy', 0):.3f}")
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            self.is_loaded = False
            raise
    
    def predict(self, text, include_probabilities=True):
        """
        Make a prediction for given text
        
        Args:
            text (str): Input text to classify
            include_probabilities (bool): Include probability distribution
            
        Returns:
            dict: Prediction results with label, confidence, and optionally probabilities
        """
        if not self.is_loaded:
            raise RuntimeError("Models not loaded. Cannot make predictions.")
        
        # Validate input
        if not text or not isinstance(text, str):
            raise ValueError("Input must be a non-empty string")
        
        text = text.strip()
        if len(text) < 10:
            raise ValueError("Text must be at least 10 characters long")
        
        try:
            # Vectorize input text
            text_vectorized = self.vectorizer.transform([text])
            
            # Make prediction
            prediction_idx = self.model.predict(text_vectorized)[0]
            predicted_label = self.label_encoder.inverse_transform([prediction_idx])[0]
            
            # Get probabilities
            probabilities = self.model.predict_proba(text_vectorized)[0]
            confidence = float(max(probabilities))
            
            # Build result
            result = {
                'prediction': predicted_label,
                'confidence': confidence,
                'model_name': self.deployment_info.get('model_name', 'gradient_boosting_tfidf_chars'),
                'model_version': self.deployment_info.get('model_version', '1.0')
            }
            
            # Add full probability distribution if requested
            if include_probabilities:
                result['probabilities'] = {
                    self.label_encoder.inverse_transform([i])[0]: float(prob)
                    for i, prob in enumerate(probabilities)
                }
            
            logger.info(f"Prediction: {predicted_label} (confidence: {confidence:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise RuntimeError(f"Failed to make prediction: {str(e)}")
    
    def predict_batch(self, texts):
        """
        Make predictions for multiple texts
        
        Args:
            texts (list): List of text strings
            
        Returns:
            list: List of prediction dictionaries
        """
        if not self.is_loaded:
            raise RuntimeError("Models not loaded")
        
        results = []
        for text in texts:
            try:
                result = self.predict(text)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to predict for text: {str(e)[:100]}")
                results.append({
                    'error': str(e),
                    'prediction': None,
                    'confidence': 0.0
                })
        
        return results
    
    def get_model_info(self):
        """Get information about the loaded model"""
        if not self.is_loaded:
            return {
                'status': 'not_loaded',
                'error': 'Models not loaded'
            }
        
        info = {
            'status': 'loaded',
            'model_name': self.deployment_info.get('model_name', 'Unknown'),
            'model_type': self.deployment_info.get('model_type', 'baseline'),
            'classes': list(self.label_encoder.classes_),
            'n_classes': len(self.label_encoder.classes_),
            'timestamp': self.deployment_info.get('timestamp', 'Unknown')
        }
        
        # Add performance metrics if available
        if self.deployment_info and 'performance' in self.deployment_info:
            info['performance'] = self.deployment_info['performance']
        
        return info
    
    def validate_prediction(self, prediction_result):
        """
        Validate that prediction result contains required fields
        
        Args:
            prediction_result (dict): Result from predict()
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['prediction', 'confidence']
        return all(field in prediction_result for field in required_fields)
    
    def get_confidence_level(self, confidence):
        """
        Categorize confidence level
        
        Args:
            confidence (float): Confidence score (0-1)
            
        Returns:
            str: 'high', 'medium', or 'low'
        """
        if confidence >= 0.8:
            return 'high'
        elif confidence >= 0.6:
            return 'medium'
        else:
            return 'low'


# Create singleton instance
_predictor_instance = None

def get_predictor(models_dir=None):
    """
    Get or create predictor singleton
    
    Args:
        models_dir (str): Optional custom models directory
        
    Returns:
        MentalHealthPredictor: Singleton predictor instance
    """
    global _predictor_instance
    
    if _predictor_instance is None:
        _predictor_instance = MentalHealthPredictor(models_dir)
    
    return _predictor_instance


# Convenience function for quick predictions
def predict_text(text):
    """
    Quick prediction function
    
    Args:
        text (str): Text to classify
        
    Returns:
        dict: Prediction result
    """
    predictor = get_predictor()
    return predictor.predict(text)