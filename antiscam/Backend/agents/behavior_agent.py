import pickle
import os
import warnings
import numpy as np
import joblib
from datetime import datetime, timedelta, timezone
from database.db import get_db

# Suppress sklearn version warnings (models trained with newer version work fine)
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

class BehaviorAgent:
    """
    Behavior Agent: Learns user transaction habits and detects anomalies
    Uses sklearn IsolationForest model trained on user transaction patterns
    Features: ["amount", "hour", "frequency", "day_of_week", "delta_hours"]
    """
    
    def __init__(self):
        # Model path - using IsolationForest model
        models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
        self.model_path = os.path.join(models_dir, 'behavior_iforest.pkl')
        
        # Load model
        self.model = None
        
        try:
            if os.path.exists(self.model_path):
                # Check file size
                model_size = os.path.getsize(self.model_path)
                if model_size == 0:
                    print(f"❌ Behavior model file is empty: {self.model_path}")
                else:
                    print(f"📦 Loading behavior model from: {self.model_path} ({model_size:,} bytes)")
                    # Load with joblib (trained in Colab)
                    try:
                        self.model = joblib.load(self.model_path)
                        print("✅ Behavior Agent IsolationForest model loaded successfully!")
                    except Exception as e:
                        print(f"❌ Could not load behavior model: {e}")
            else:
                print(f"⚠️  Behavior model not found at: {self.model_path}")
                print("   Looking for: behavior_iforest.pkl")
                print("   Behavior Agent will use rule-based fallback.")
        except Exception as e:
            print(f"❌ Error loading behavior model: {e}")
            print("   Using rule-based analysis as fallback.")
    
    def analyze(self, transaction):
        """
        Analyze transaction against user's normal behavior patterns using IsolationForest
        
        Args:
            transaction: dict with 'user_id', 'amount', 'time', etc.
        
        Returns:
            dict with risk_score, message, details, evidence
        """
        user_id = transaction.get('user_id', '')
        amount = float(transaction.get('amount', 0))
        time_str = transaction.get('time', '')
        
        # Get user behavior history
        user_pattern = self._get_user_pattern(user_id)
        
        # If model exists, use IsolationForest for anomaly detection
        if self.model:
            try:
                features = self._extract_features(transaction, user_pattern)
                
                # IsolationForest returns: -1 for anomalies, 1 for normal
                prediction = self.model.predict([features])[0]
                anomaly_score = self.model.score_samples([features])[0]
                
                # Convert to risk score (0-100)
                # IsolationForest: lower anomaly_score = more anomalous
                # Score is typically negative for anomalies, close to 0 or positive for normal
                # We'll map: anomaly_score < -0.1 → high risk, -0.1 to 0 → medium, > 0 → low
                
                if prediction == -1:  # Anomaly detected
                    # High risk if predicted as anomaly
                    if anomaly_score < -0.2:
                        risk_score = 85
                    elif anomaly_score < -0.1:
                        risk_score = 70
                    else:
                        risk_score = 60
                else:  # Normal behavior (prediction == 1)
                    # Low risk for normal behavior
                    if anomaly_score > 0.1:
                        risk_score = 15
                    elif anomaly_score > 0:
                        risk_score = 25
                    else:
                        risk_score = 35
                
                risk_score = min(max(risk_score, 0), 100)  # Clamp to 0-100
                
            except Exception as e:
                print(f"Error in behavior model prediction: {e}")
                # Fallback to rule-based if model fails
                risk_score = self._rule_based_analysis(transaction, user_pattern)
        else:
            # No model available - use rule-based fallback
            print("Behavior IsolationForest model not available. Using rule-based analysis.")
            risk_score = self._rule_based_analysis(transaction, user_pattern)
        
        # Generate explanation
        evidence = []
        message = "Transaction matches your normal patterns"
        
        if risk_score >= 70:
            message = "🚨 Unusual behavior detected!"
            evidence.append("IsolationForest model detected significant deviation from your typical transaction patterns")
        elif risk_score >= 40:
            message = "⚠️ Somewhat unusual activity"
            evidence.append("IsolationForest model detected minor deviation from normal patterns")
        else:
            message = "✓ Behavior matches your normal patterns"
            evidence.append("Transaction matches your historical behavior patterns")
        
        # Add specific evidence
        if user_pattern:
            if amount > user_pattern.get('avg_amount', 0) * 2:
                evidence.append(f"Amount (₹{amount}) is much higher than your average (₹{user_pattern.get('avg_amount', 0):.0f})")
            
            if time_str:
                hour = self._extract_hour(time_str)
                if hour and (hour < 6 or hour > 23):
                    evidence.append(f"Transaction time ({time_str}) is unusual - you rarely transact at this hour")
        
        details = f"""
        Analyzed transaction against your historical behavior patterns using IsolationForest anomaly detection.
        {'This transaction shows significant anomalies compared to your normal activity.' if risk_score >= 40 else 'This transaction aligns with your typical transaction patterns.'}
        Behavior analysis helps detect if you're acting under unusual circumstances.
        """
        
        # Update user behavior pattern
        self._update_user_pattern(user_id, amount, time_str)
        
        return {
            'risk_score': round(risk_score, 1),
            'message': message,
            'details': details.strip(),
            'evidence': evidence
        }
    
    def _get_user_pattern(self, user_id):
        """Get user's historical behavior pattern"""
        db = get_db()
        user_behavior = db.user_behavior
        
        pattern = user_behavior.find_one({"user_id": user_id})
        
        if pattern:
            return {
                'avg_amount': pattern.get('avg_amount', 0) or 0,
                'transaction_count': pattern.get('transaction_count', 0) or 0,
                'last_transaction_at': pattern.get('last_transaction_at'),
                'common_times': pattern.get('common_times', '') or ''
            }
        return None
    
    def _extract_features(self, transaction, user_pattern):
        """
        Extract features for IsolationForest model
        Features must match training: ["amount", "hour", "frequency", "day_of_week", "delta_hours"]
        
        Returns:
            numpy array: [amount, hour, frequency, day_of_week, delta_hours]
        """
        amount = float(transaction.get('amount', 0))
        time_str = transaction.get('time', '')
        
        # Extract hour (0-23)
        hour = self._extract_hour(time_str) or 12  # Default to noon
        
        # Frequency: transactions per day (estimate from transaction_count)
        # For simplicity, use transaction_count / 30 as frequency (assuming ~1 month of history)
        transaction_count = user_pattern.get('transaction_count', 0) if user_pattern else 0
        frequency = min(transaction_count / 30.0, 5.0) if transaction_count > 0 else 0.0  # Cap at 5
        
        # Day of week (0=Monday, 6=Sunday)
        # Get current day or from transaction time if available
        now = datetime.now(timezone.utc)
        day_of_week = now.weekday()
        
        # Delta hours: hours since last transaction
        if user_pattern and user_pattern.get('last_transaction_at'):
            try:
                # Handle both datetime objects and strings
                last_tx = user_pattern.get('last_transaction_at')
                if isinstance(last_tx, str):
                    # Try parsing ISO format or common string formats
                    try:
                        last_tx = datetime.fromisoformat(last_tx.replace('Z', '+00:00'))
                    except:
                        # Try other formats
                        from dateutil.parser import parse
                        last_tx = parse(last_tx)
                elif isinstance(last_tx, datetime):
                    pass  # Already datetime
                else:
                    last_tx = None
                
                if last_tx:
                    delta = (now - last_tx).total_seconds() / 3600  # Convert to hours
                    delta_hours = min(delta, 168.0)  # Cap at 1 week (168 hours)
                else:
                    delta_hours = 24.0  # Default: 1 day ago
            except:
                delta_hours = 24.0  # Default: 1 day ago
        else:
            # No previous transaction
            delta_hours = 168.0  # Default: 1 week (first transaction)
        
        # Return features in same order as training
        return np.array([
            amount,
            float(hour),
            frequency,
            float(day_of_week),
            delta_hours
        ])
    
    def _rule_based_analysis(self, transaction, user_pattern):
        """Fallback rule-based behavior analysis"""
        risk = 20  # Base risk
        
        amount = float(transaction.get('amount', 0))
        time_str = transaction.get('time', '')
        
        if user_pattern:
            avg_amount = user_pattern.get('avg_amount', 0)
            
            # Amount anomaly
            if avg_amount > 0:
                if amount > avg_amount * 3:
                    risk += 40
                elif amount > avg_amount * 2:
                    risk += 25
                elif amount > avg_amount * 1.5:
                    risk += 10
            
            # Time anomaly
            hour = self._extract_hour(time_str)
            if hour:
                if hour < 6 or hour >= 23:  # Late night / early morning
                    risk += 30
                elif hour < 9:  # Very early morning
                    risk += 15
        else:
            # First transaction - moderate risk
            risk = 30
        
        return min(risk, 95)
    
    def _extract_hour(self, time_str):
        """Extract hour from time string (e.g., '2:05 AM' -> 2)"""
        try:
            # Handle formats like "2:05 AM", "14:30", etc.
            if 'AM' in time_str.upper() or 'PM' in time_str.upper():
                time_part = time_str.split()[0]
                hour = int(time_part.split(':')[0])
                if 'PM' in time_str.upper() and hour != 12:
                    hour += 12
                elif 'AM' in time_str.upper() and hour == 12:
                    hour = 0
                return hour
            else:
                return int(time_str.split(':')[0])
        except:
            return None
    
    def _update_user_pattern(self, user_id, amount, time_str):
        """Update user behavior pattern in database"""
        db = get_db()
        user_behavior = db.user_behavior
        
        # Get existing pattern
        existing = user_behavior.find_one({"user_id": user_id})
        now = datetime.now(timezone.utc)
        
        if existing:
            # Update existing
            new_count = existing.get('transaction_count', 0) + 1
            old_avg = existing.get('avg_amount', 0) or 0
            old_count = existing.get('transaction_count', 1) or 1
            new_avg = ((old_avg * old_count) + amount) / new_count
            
            user_behavior.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "avg_amount": new_avg,
                        "transaction_count": new_count,
                        "last_transaction_at": now
                    }
                }
            )
        else:
            # Create new
            user_behavior.insert_one({
                "user_id": user_id,
                "avg_amount": amount,
                "transaction_count": 1,
                "last_transaction_at": now,
                "common_times": ""
            })
