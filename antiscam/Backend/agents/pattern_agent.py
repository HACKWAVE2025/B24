import pickle
import os
import warnings
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline

# Suppress sklearn version warnings (models trained with newer version work fine)
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

class PatternAgent:
    """
    Pattern Agent: Detects known scam text patterns and keywords
    Uses ML model trained on synthetic scam text dataset
    """
    
    def __init__(self):
        # Try both possible filenames
        model_path1 = os.path.join(os.path.dirname(__file__), '..', 'models', 'pattern_agent_tiny.pkl')

        
        # Load ML model Pipeline (trained in Colab)
        # Pipeline combines vectorizer + classifier in one file
        self.model = None
        model_path = None
        
        # Try pattern_agent_tiny.pkl first (from your Colab)
        if os.path.exists(model_path1):
            model_path = model_path1
        
        if model_path:
            try:
                # Check file size first
                file_size = os.path.getsize(model_path)
                if file_size == 0:
                    print(f"❌ Pattern model file is empty: {model_path}")
                    return
                
                print(f"📦 Loading pattern model from: {model_path} ({file_size:,} bytes)")
                
                # Try joblib first (from Colab), then pickle as fallback
                try:
                    self.model = joblib.load(model_path)
                    print(f"✅ Pattern Agent model loaded with joblib!")
                except Exception as joblib_error:
                    print(f"⚠️  Joblib failed, trying pickle: {joblib_error}")
                    with open(model_path, 'rb') as f:
                        self.model = pickle.load(f)
                    print(f"✅ Pattern Agent model loaded with pickle!")
                
                # Verify the model is properly fitted
                if self.model:
                    self._verify_model()
                
            except pickle.UnpicklingError as e:
                print(f"❌ Pattern model file is not a valid pickle file: {e}")
                print(f"   File path: {model_path}")
                print("   Make sure the file was saved using joblib.dump() or pickle.dump()")
            except Exception as e:
                print(f"❌ Could not load pattern model: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("Pattern model not found. Looking for: pattern_agent_tiny.pkl or pattern_model.pkl")
            # Create a fallback model if none is found
            self._create_fallback_model()
    
    def _verify_model(self):
        """Verify that the model is properly fitted"""
        try:
            # Check if it's a pipeline with a fitted vectorizer
            if self.model and hasattr(self.model, 'named_steps'):
                # It's a pipeline, check if vectorizer is fitted
                if 'tfidf' in self.model.named_steps:
                    vectorizer = self.model.named_steps['tfidf']
                    if hasattr(vectorizer, 'vocabulary_'):
                        print("✅ Model verified - TF-IDF vectorizer is fitted")
                    else:
                        print("⚠️  Warning: TF-IDF vectorizer is not fitted")
                        self.model = None
                        self._create_fallback_model()
                        return
                else:
                    print("✅ Model verified - no TF-IDF step found")
            elif self.model:
                print("✅ Model verified - not a pipeline")
            print("✅ Pattern Agent model loaded successfully!")
        except Exception as e:
            print(f"⚠️  Model verification failed: {e}")
            self.model = None
            self._create_fallback_model()
    
    def _create_fallback_model(self):
        """Create a simple fallback model if the main model fails"""
        print("⚠️  Creating fallback pattern detection model")
        
        # Create a simple rule-based approach as fallback
        # This is not as accurate as the ML model but will prevent errors
        self.fallback_keywords = [
            'urgent', 'immediate', 'asap', 'hurry', 'quick', 'fast',
            'loan', 'credit', 'money', 'cash', 'fund', 'payment',
            'help', 'assist', 'support', 'service',
            'verify', 'confirm', 'authenticate', 'validate',
            'account', 'bank', 'upi', 'wallet',
            'winner', 'prize', 'lottery', 'gift', 'free',
            'government', 'official', 'authority',
            'password', 'otp', 'pin', 'code',
            'threat', 'warning', 'alert', 'danger'
        ]
    
    def analyze(self, transaction):
        """
        Analyze transaction for scam patterns
        
        Args:
            transaction: dict with 'reason', 'receiver', etc.
        
        Returns:
            dict with risk_score, message, details, evidence
        """
        text = f"{transaction.get('reason', '')} {transaction.get('receiver', '')}".lower()
        
        # If model exists and is valid, use it (trained in Colab as Pipeline)
        if self.model:
            try:
                # Pipeline handles text directly (vectorizer + classifier combined)
                risk_score = self.model.predict_proba([text])[0][1] * 100
            except Exception as e:
                print(f"Error in pattern model prediction: {e}")
                # Fall back to keyword-based approach
                risk_score = self._fallback_analysis(text)
        else:
            # Use fallback analysis if no model available
            risk_score = self._fallback_analysis(text)
        
        # Generate explanation
        evidence = []
        message = "Transaction appears safe"
        
        if risk_score >= 70:
            message = "⚠️ High scam risk detected!"
            evidence.append("High-risk scam patterns detected in transaction text")
            evidence.append("Text analysis indicates suspicious content")
        elif risk_score >= 40:
            message = "⚠️ Medium risk - proceed with caution"
            evidence.append("Some suspicious patterns detected")
        else:
            message = "✓ Pattern analysis shows low risk"
            evidence.append("No significant scam patterns detected")
        
        details = f"""
        Analyzed transaction text for known scam patterns.
        {'Detected patterns that match known scam tactics.' if risk_score >= 40 else 'No red flags found in text analysis.'}
        Pattern detection uses machine learning and keyword analysis.
        """
        
        return {
            'risk_score': round(risk_score, 1),
            'message': message,
            'details': details.strip(),
            'evidence': evidence
        }
    
    def _fallback_analysis(self, text):
        """Fallback keyword-based analysis"""
        if not hasattr(self, 'fallback_keywords'):
            return 30  # Neutral score if no fallback available
            
        # Count matching keywords
        matches = sum(1 for keyword in self.fallback_keywords if keyword in text)
        
        # Convert to risk score (0-100)
        # Max score at 10+ matches
        risk_score = min(100, matches * 10)
        
        return risk_score