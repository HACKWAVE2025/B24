import os
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

def retrain_behavior_model():
    base_dir = os.path.dirname(__file__)
    data_path = os.path.join(base_dir, '..', 'data', 'behavior_dataset.csv')
    model_path = os.path.join(base_dir, '..', 'models', 'behavior_iforest.pkl')

    print(f"📂 Looking for dataset at: {data_path}")

    if not os.path.exists(data_path):
        print("❌ Dataset not found! Please ensure behavior_dataset.csv exists in /data.")
        return

    df = pd.read_csv(data_path)
    print(f"📊 Loaded dataset with shape: {df.shape}")

    required_features = ["amount", "hour", "frequency", "day_of_week", "delta_hours"]
    if not all(col in df.columns for col in required_features):
        print(f"❌ Missing columns! Found: {list(df.columns)}")
        return

    X = df[required_features].values
    print(f"✅ Training model on {len(X)} samples...")

    model = IsolationForest(n_estimators=100, contamination=0.07, random_state=42)
    model.fit(X)

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)

    print(f"✅ Retrained and saved model on {len(df)} samples → {model_path}")

if __name__ == "__main__":
    retrain_behavior_model()
