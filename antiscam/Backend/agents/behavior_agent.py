import os
import warnings
import numpy as np
import joblib
<<<<<<< HEAD
from datetime import datetime, timedelta, timezone
=======
import pandas as pd
from datetime import datetime
from sklearn.ensemble import IsolationForest
>>>>>>> 8b231281e303f9616859ac75b7ed2821ac187f70
from database.db import get_db

# Suppress sklearn warnings
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')


class BehaviorAgent:
    """
    Behavior Agent:
    - Detects anomalies using IsolationForest.
    - Stores user feedback locally (data/behavior_dataset.csv).
    - Retrains automatically after threshold feedbacks (default: 10).
    """

    def __init__(self):
        base_dir = os.path.dirname(__file__)
        self.models_dir = os.path.join(base_dir, '..', 'models')
        self.data_dir = os.path.join(base_dir, '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)

        # File paths
        self.model_path = os.path.join(self.models_dir, 'behavior_iforest.pkl')
        self.dataset_path = os.path.join(self.data_dir, 'behavior_dataset.csv')
        self.feedback_counter_path = os.path.join(self.data_dir, 'feedback_counter.txt')

        self.threshold = 10
        self.model = None
        self._load_model()

    # ------------------- MODEL MANAGEMENT -------------------
    def _load_model(self):
        """Load IsolationForest model if available."""
        try:
            if os.path.exists(self.model_path) and os.path.getsize(self.model_path) > 0:
                print(f"📦 Loading Behavior model → {self.model_path}")
                self.model = joblib.load(self.model_path)
                print("✅ IsolationForest model loaded successfully!")
            else:
                print(f"⚠️ No valid model found. Run retrain_behavior_manual.py first.")
                self.model = None
        except Exception as e:
            print(f"❌ Could not load model: {e}")
            self.model = None

    def reload_model(self):
        """Reloads the model after retraining."""
        print("🔁 Reloading updated model...")
        self._load_model()

    # ------------------- MAIN ANALYSIS -------------------
    def analyze(self, transaction):
        """Analyze a transaction using the IsolationForest or fallback."""
        try:
            user_id = transaction.get('user_id', '')
            amount = float(transaction.get('amount', 0))
            time_str = transaction.get('time', '')

            user_pattern = self._get_user_pattern(user_id)
            features = self._extract_features(transaction, user_pattern)

            if self.model:
                prediction = self.model.predict([features])[0]
                score = self.model.score_samples([features])[0]

                if prediction == -1:
                    risk_score = 80 if score < -0.2 else 65
                else:
                    risk_score = 25 if score > 0.1 else 35
            else:
                print("⚠️ No model found — using fallback rules.")
                risk_score = self._rule_based_analysis(transaction, user_pattern)

            message, evidence = self._generate_message(risk_score, amount, time_str, user_pattern)
            self._update_user_pattern(user_id, amount, time_str)

            return {
                "risk_score": round(risk_score, 1),
                "message": message,
                "details": "Analyzed using IsolationForest-based anomaly detection.",
                "evidence": evidence
            }

        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            return {
                "risk_score": 50,
                "message": "Error during behavior analysis.",
                "details": str(e)
            }

    # ------------------- FEEDBACK & RETRAINING -------------------
    def add_feedback(self, feedback):
        """
        Add new feedback to dataset.
        Example feedback = {"amount": 1200, "hour": 14, "frequency": 3, "day_of_week": 2, "delta_hours": 5}
        """
        df = pd.DataFrame([feedback])
        df.to_csv(self.dataset_path, mode='a', header=not os.path.exists(self.dataset_path), index=False)
        print(f"🧾 Feedback added: {feedback}")

        count = self._increment_feedback_count()
        if count >= self.threshold:
            print("⚡ Feedback threshold reached — retraining model...")
            self._retrain_from_csv()
            self._reset_feedback_count()

    def _increment_feedback_count(self):
        count = 0
        if os.path.exists(self.feedback_counter_path):
            try:
                with open(self.feedback_counter_path, 'r') as f:
                    count = int(f.read().strip())
            except:
                count = 0
        count += 1
        with open(self.feedback_counter_path, 'w') as f:
            f.write(str(count))
        return count

    def _reset_feedback_count(self):
        with open(self.feedback_counter_path, 'w') as f:
            f.write("0")
        print("🔄 Feedback counter reset.")

    def _retrain_from_csv(self):
        """Retrains IsolationForest using local dataset CSV."""
        if not os.path.exists(self.dataset_path):
            print("⚠️ No dataset found for retraining.")
            return

        df = pd.read_csv(self.dataset_path)
        features = ["amount", "hour", "frequency", "day_of_week", "delta_hours"]

        if not all(col in df.columns for col in features):
            print("❌ Dataset missing columns for retraining.")
            return

        X = df[features].values
        model = IsolationForest(n_estimators=100, contamination=0.07, random_state=42)
        model.fit(X)

        joblib.dump(model, self.model_path)
        self.model = model
        print(f"✅ Retrained model on {len(df)} samples → saved to {self.model_path}")

    # ------------------- UTILITIES -------------------
    def _get_user_pattern(self, user_id):
        db = get_db()
        return db.user_behavior.find_one({"user_id": user_id}) or None

    def _extract_features(self, transaction, user_pattern):
        """Extracts consistent 5 features."""
        amount = float(transaction.get('amount', 0))
        time_str = transaction.get('time', '')
        hour = self._extract_hour(time_str) or 12

        # Frequency & delta logic
        transaction_count = user_pattern.get('transaction_count', 0) if user_pattern else 0
<<<<<<< HEAD
        frequency = min(transaction_count / 30.0, 5.0) if transaction_count > 0 else 0.0  # Cap at 5
        
        # Day of week (0=Monday, 6=Sunday)
        # Get current day or from transaction time if available
        now = datetime.now(timezone.utc)
        day_of_week = now.weekday()
        
        # Delta hours: hours since last transaction
=======
        frequency = min(transaction_count / 30.0, 5.0) if transaction_count > 0 else 0.0
        day_of_week = datetime.utcnow().weekday()

>>>>>>> 8b231281e303f9616859ac75b7ed2821ac187f70
        if user_pattern and user_pattern.get('last_transaction_at'):
            try:
                from dateutil.parser import parse
                last_tx = parse(user_pattern['last_transaction_at']) if isinstance(user_pattern['last_transaction_at'], str) else user_pattern['last_transaction_at']
                delta_hours = min((datetime.utcnow() - last_tx).total_seconds() / 3600, 168.0)
            except:
                delta_hours = 24.0
        else:
            delta_hours = 168.0

        return np.array([amount, float(hour), frequency, float(day_of_week), delta_hours])

    def _extract_hour(self, time_str):
        try:
            if 'AM' in time_str.upper() or 'PM' in time_str.upper():
                hour = int(time_str.split(':')[0])
                if 'PM' in time_str.upper() and hour != 12:
                    hour += 12
                elif 'AM' in time_str.upper() and hour == 12:
                    hour = 0
                return hour
            return int(time_str.split(':')[0])
        except:
            return None
<<<<<<< HEAD
    
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
=======

    def _generate_message(self, risk_score, amount, time_str, user_pattern):
        evidence = []
        if risk_score >= 70:
            message = "🚨 Unusual behavior detected!"
            evidence.append("Model detected strong deviation from usual patterns.")
        elif risk_score >= 40:
            message = "⚠️ Somewhat unusual activity."
            evidence.append("Minor deviation detected.")
>>>>>>> 8b231281e303f9616859ac75b7ed2821ac187f70
        else:
            message = "✓ Normal behavior detected."
            evidence.append("Transaction matches usual behavior.")

        if user_pattern:
            avg = user_pattern.get('avg_amount', 0)
            if amount > avg * 2:
                evidence.append(f"Amount ₹{amount} > 2x your average ₹{avg:.0f}")
            hour = self._extract_hour(time_str)
            if hour and (hour < 6 or hour > 23):
                evidence.append(f"Unusual transaction hour: {time_str}")

        return message, evidence

    def _update_user_pattern(self, user_id, amount, time_str):
        db = get_db()
        coll = db.user_behavior
        now = datetime.utcnow()

        existing = coll.find_one({"user_id": user_id})
        if existing:
            new_count = existing.get('transaction_count', 0) + 1
            old_avg = existing.get('avg_amount', 0)
            new_avg = ((old_avg * existing.get('transaction_count', 1)) + amount) / new_count
            coll.update_one({"user_id": user_id}, {"$set": {"avg_amount": new_avg, "transaction_count": new_count, "last_transaction_at": now}})
        else:
            coll.insert_one({
                "user_id": user_id,
                "avg_amount": amount,
                "transaction_count": 1,
                "last_transaction_at": now
            })
