"""
DeepMindCheck ML Models Package
Production mental health text classification
"""

from .predictor import get_predictor, predict_text, MentalHealthPredictor

__all__ = ['get_predictor', 'predict_text', 'MentalHealthPredictor']