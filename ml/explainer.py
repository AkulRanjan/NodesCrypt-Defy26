"""
Explainability Module
Provides human-readable explanations for ML/RL decisions using SHAP.

Features:
- SHAP-based feature importance
- Human-readable decision explanations
- Explanation hashing for audit
"""
import hashlib
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Try to import SHAP (optional dependency)
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class ExplanationResult:
    """Result of an explanation request."""
    
    def __init__(self):
        self.features: Dict[str, float] = {}
        self.feature_contributions: Dict[str, float] = {}
        self.top_features: List[Tuple[str, float]] = []
        self.decision_reason: str = ""
        self.confidence: float = 0.0
        self.model_type: str = ""
        self.explanation_hash: str = ""
        self.timestamp: str = ""
        
    def to_dict(self) -> dict:
        return {
            "features": self.features,
            "feature_contributions": self.feature_contributions,
            "top_features": self.top_features,
            "decision_reason": self.decision_reason,
            "confidence": self.confidence,
            "model_type": self.model_type,
            "explanation_hash": self.explanation_hash,
            "timestamp": self.timestamp
        }
    
    def get_summary(self) -> str:
        """Get one-line human-readable summary."""
        if not self.top_features:
            return self.decision_reason
        
        top = self.top_features[:3]
        factors = ", ".join([f"{name}: {val:.2f}" for name, val in top])
        return f"{self.decision_reason} (Key factors: {factors})"


class Explainer:
    """
    Provides explanations for ML model decisions.
    """
    
    FEATURE_DESCRIPTIONS = {
        "fee_rate": "Transaction fee relative to data size",
        "data_size": "Size of transaction payload",
        "nonce_gap": "Gap between current and expected nonce",
        "sender_tx_count": "Number of transactions from sender in mempool",
        "sender_avg_fee": "Average fee rate of sender's transactions",
        "spam_score": "ML-predicted spam probability",
        "congestion_score": "Current mempool congestion level",
        "reputation_score": "Address reputation score",
        "is_blacklisted": "Whether address is blacklisted",
        "simulation_risk": "Risk score from transaction simulation"
    }
    
    def __init__(self, model=None):
        self.model = model
        self.shap_explainer = None
        
        if SHAP_AVAILABLE and model is not None:
            try:
                self.shap_explainer = shap.TreeExplainer(model)
            except:
                pass
    
    def explain(self, features: dict, prediction: float, model_type: str = "xgboost") -> ExplanationResult:
        """
        Generate explanation for a prediction.
        
        Args:
            features: Input features as dict
            prediction: Model prediction value
            model_type: Type of model used
            
        Returns:
            ExplanationResult with explanation data
        """
        result = ExplanationResult()
        result.features = features
        result.confidence = 1.0 - abs(0.5 - prediction) * 2  # Confidence based on prediction certainty
        result.model_type = model_type
        result.timestamp = datetime.utcnow().isoformat()
        
        # Calculate feature contributions (simplified without SHAP)
        contributions = self._calculate_contributions(features, prediction)
        result.feature_contributions = contributions
        
        # Get top features
        sorted_features = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
        result.top_features = sorted_features[:5]
        
        # Generate human-readable reason
        result.decision_reason = self._generate_reason(prediction, sorted_features[:3])
        
        # Generate hash for audit
        result.explanation_hash = self._hash_explanation(result)
        
        return result
    
    def _calculate_contributions(self, features: dict, prediction: float) -> Dict[str, float]:
        """
        Calculate feature contributions to the prediction.
        Uses SHAP if available, otherwise uses a heuristic approach.
        """
        if self.shap_explainer and NUMPY_AVAILABLE:
            try:
                import numpy as np
                X = np.array([[features.get(k, 0) for k in sorted(features.keys())]])
                shap_values = self.shap_explainer.shap_values(X)
                
                contributions = {}
                for i, key in enumerate(sorted(features.keys())):
                    contributions[key] = float(shap_values[0][i]) if i < len(shap_values[0]) else 0
                return contributions
            except:
                pass
        
        # Heuristic-based contributions (fallback)
        contributions = {}
        
        # Higher values of certain features contribute more to spam score
        spam_indicators = ["sender_tx_count", "nonce_gap", "is_blacklisted"]
        safe_indicators = ["reputation_score", "fee_rate"]
        
        for key, value in features.items():
            if key in spam_indicators:
                contributions[key] = float(value) * 0.2 * prediction
            elif key in safe_indicators:
                contributions[key] = -float(value) * 0.1 * prediction
            else:
                contributions[key] = float(value) * 0.05 * prediction
        
        return contributions
    
    def _generate_reason(self, prediction: float, top_features: List[Tuple[str, float]]) -> str:
        """Generate human-readable decision reason."""
        if prediction >= 0.8:
            risk_level = "very high risk"
        elif prediction >= 0.6:
            risk_level = "high risk"
        elif prediction >= 0.4:
            risk_level = "moderate risk"
        elif prediction >= 0.2:
            risk_level = "low risk"
        else:
            risk_level = "very low risk"
        
        if not top_features:
            return f"Transaction classified as {risk_level}"
        
        # Get top contributing factor
        top_name, top_value = top_features[0]
        description = self.FEATURE_DESCRIPTIONS.get(top_name, top_name)
        
        if top_value > 0:
            return f"Transaction classified as {risk_level}, primarily due to {description.lower()}"
        else:
            return f"Transaction classified as {risk_level}, despite {description.lower()} being favorable"
    
    def _hash_explanation(self, result: ExplanationResult) -> str:
        """Generate hash of explanation for audit."""
        data = json.dumps({
            "features": result.features,
            "contributions": result.feature_contributions,
            "reason": result.decision_reason,
            "timestamp": result.timestamp
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()
    
    def explain_rule_match(self, rule_result: dict, context: dict) -> ExplanationResult:
        """Generate explanation for a rule match."""
        result = ExplanationResult()
        result.features = context
        result.confidence = 1.0  # Rules are deterministic
        result.model_type = "rule"
        result.timestamp = datetime.utcnow().isoformat()
        
        result.decision_reason = f"Rule '{rule_result['rule_id']}' matched: {rule_result.get('reason', 'No reason provided')}"
        
        # The rule's matched fields are the top features
        result.top_features = [
            (rule_result.get("category", "rule"), rule_result.get("risk_score", 0.5))
        ]
        
        result.explanation_hash = self._hash_explanation(result)
        
        return result
    
    def get_feature_description(self, feature_name: str) -> str:
        """Get human-readable description of a feature."""
        return self.FEATURE_DESCRIPTIONS.get(feature_name, feature_name)


# Singleton instance
_explainer = None

def get_explainer(model=None) -> Explainer:
    global _explainer
    if _explainer is None or model is not None:
        _explainer = Explainer(model)
    return _explainer

def explain_prediction(features: dict, prediction: float) -> ExplanationResult:
    """Convenience function for explaining a prediction."""
    return get_explainer().explain(features, prediction)


if __name__ == "__main__":
    print("=" * 60)
    print("[EXPLAINABILITY] Module Test")
    print("=" * 60)
    
    explainer = Explainer()
    
    # Test explanation
    test_features = {
        "fee_rate": 0.001,
        "data_size": 100,
        "nonce_gap": 5,
        "sender_tx_count": 15,
        "sender_avg_fee": 0.002,
        "reputation_score": 0.3,
        "is_blacklisted": 0
    }
    
    result = explainer.explain(test_features, prediction=0.75)
    
    print(f"\nExplanation Result:")
    print(f"  Reason: {result.decision_reason}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Top Features:")
    for name, value in result.top_features[:3]:
        print(f"    - {name}: {value:.4f}")
    print(f"  Summary: {result.get_summary()}")
    print(f"  Hash: {result.explanation_hash[:16]}...")
