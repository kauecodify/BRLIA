import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
import redis
from sklearn.preprocessing import StandardScaler

class RealTimeFraudDetector:
    def __init__(self):
        self.model = load_model('models/fraud_lstm_v3.h5')
        self.scaler = joblib.load('models/scaler.pkl')
        self.redis_client = redis.Redis(host='redis-ai', port=6379)
        self.feature_columns = [
            'transaction_amount', 'time_since_last_tx', 'merchant_risk_score',
            'velocity_1h', 'velocity_24h', 'location_anomaly', 'device_risk'
        ]
    
    def predict(self, transaction_data: dict) -> dict:
        # enriquecimento com features em tempo real do redis
        enriched = self._enrich_features(transaction_data)
        scaled = self.scaler.transform([enriched])
        
        # predição com incerteza bayesiana
        predictions = []
        for _ in range(10):  # Monte Carlo Dropout
            predictions.append(self.model(scaled, training=True).numpy()[0][0])
        
        risk_score = np.mean(predictions)
        uncertainty = np.std(predictions)
        
        # decisão adaptativa com threshold dinâmico
        threshold = self._get_dynamic_threshold(transaction_data['merchant_category'])
        is_fraud = risk_score > threshold
        
        return {
            'risk_score': float(risk_score),
            'uncertainty': float(uncertainty),
            'is_fraud': bool(is_fraud),
            'confidence': 1 - uncertainty,
            'model_version': 'v3.2',
            'explanation': self._generate_shap_explanation(enriched)
        }
    
    def _get_dynamic_threshold(self, category: str) -> float:
        """Threshold adaptativo por categoria de merchant"""
        base_thresholds = {
            'ecommerce': 0.75,
            'food': 0.65,
            'travel': 0.82,
            'digital_goods': 0.78
        }
        return base_thresholds.get(category, 0.7)