import pickle
import os
import warnings
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline

warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

class PatternAgent:
    """
    Pattern Agent – Detects scam-related patterns in text using ML or keyword fallback
    """

    def __init__(self):
        self.model = None
        self._load_model_or_fallback()

    def _load_model_or_fallback(self):
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'pattern_agent_tiny.pkl')

        if not os.path.exists(model_path):
            print("⚠️ No ML model found, using fallback keyword detection.")
            self._create_fallback_model()
            return

        try:
            file_size = os.path.getsize(model_path)
            if file_size == 0:
                print("❌ Empty model file detected.")
                self._create_fallback_model()
                return

            print(f"📦 Loading Pattern Agent model from: {model_path}")
            try:
                self.model = joblib.load(model_path)
                print("✅ Loaded model using joblib.")
            except Exception:
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print("✅ Loaded model using pickle.")

            self._verify_model()

        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            self._create_fallback_model()

    def _verify_model(self):
        if not self.model:
            self._create_fallback_model()
            return

        if hasattr(self.model, 'named_steps') and 'tfidf' in self.model.named_steps:
            vectorizer = self.model.named_steps['tfidf']
            if hasattr(vectorizer, 'vocabulary_'):
                print("✅ TF-IDF vectorizer is fitted and verified.")
            else:
                print("⚠️ Vectorizer not fitted — switching to fallback.")
                self._create_fallback_model()
        else:
            print("✅ Pattern Agent model verified successfully.")

    def _create_fallback_model(self):
        print("⚠️ Using fallback keyword-based scam detection.")
        self.fallback_keywords = [
            'urgent', 'immediate', 'asap', 'loan', 'credit', 'fund', 'money',
            'help', 'assist', 'verify', 'account', 'bank', 'upi', 'password',
            'otp', 'winner', 'lottery', 'gift', 'free', 'alert', 'warning'
        ]

    def analyze(self, transaction):
        text = f"{transaction.get('reason', '')} {transaction.get('receiver', '')}".lower()

        if self.model:
            try:
                risk_score = self.model.predict_proba([text])[0][1] * 100
            except Exception as e:
                print(f"⚠️ Prediction error: {e}")
                risk_score = self._fallback_analysis(text)
        else:
            risk_score = self._fallback_analysis(text)

        message, evidence = self._generate_message(risk_score)

        return {
            'risk_score': round(risk_score, 1),
            'message': message,
            'details': "Analyzed transaction text for scam patterns using ML or keyword analysis.",
            'evidence': evidence
        }

    def _fallback_analysis(self, text):
        matches = sum(1 for kw in self.fallback_keywords if kw in text)
        return min(100, matches * 10)

    def _generate_message(self, risk_score):
        if risk_score >= 70:
            return ("⚠️ High scam risk detected!", ["Multiple scam keywords found."])
        elif risk_score >= 40:
            return ("⚠️ Medium risk — review before proceeding.", ["Some scam-related words detected."])
        else:
            return ("✓ Low scam risk", ["No significant scam indicators found."])
