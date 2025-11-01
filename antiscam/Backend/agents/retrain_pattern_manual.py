import pandas as pd
import joblib
import os
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


def retrain_pattern_model():
    data_path = os.path.join(os.path.dirname(__file__), "../data/pattern_data.csv")
    model_path = os.path.join(os.path.dirname(__file__), "pattern_model.pkl")

    print(f"📂 Looking for dataset at: {data_path}")
    if not os.path.exists(data_path):
        print("❌ Dataset not found, aborting retrain.")
        return

    df = pd.read_csv(data_path)
    print(f"📊 Loaded dataset with shape: {df.shape}")

    if not {'description', 'is_scam'}.issubset(df.columns):
        print(f"❌ Missing columns! Found: {list(df.columns)}")
        return

    # -------------------------------------------------------------
    # 🧠 Feature engineering from text
    # -------------------------------------------------------------
    print("🔧 Generating text-based features...")

    df["desc_length"] = df["description"].apply(len)
    df["num_words"] = df["description"].apply(lambda x: len(str(x).split()))
    df["num_digits"] = df["description"].apply(lambda x: sum(c.isdigit() for c in str(x)))
    df["num_links"] = df["description"].apply(lambda x: len(re.findall(r"http|www", str(x))))
    df["has_urgent_word"] = df["description"].apply(
        lambda x: 1 if re.search(r"urgent|immediate|alert|verify|account", str(x), re.I) else 0
    )

    # Vectorize limited vocab (optional small text features)
    vectorizer = CountVectorizer(max_features=20, stop_words="english")
    text_features = vectorizer.fit_transform(df["description"]).toarray()
    text_feature_names = [f"word_{w}" for w in vectorizer.get_feature_names_out()]

    text_df = pd.DataFrame(text_features, columns=text_feature_names)

    # Combine numeric + text features
    full_df = pd.concat([df, text_df], axis=1)

    # Rename label column
    full_df = full_df.rename(columns={"is_scam": "label"})

    # Drop unused
    X = full_df.drop(columns=["description", "label"])
    y = full_df["label"]

    # -------------------------------------------------------------
    # 🧪 Train/test split & model training
    # -------------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    acc = accuracy_score(y_test, model.predict(X_test))
    print(f"✅ Pattern model retrained successfully — Accuracy: {acc:.2f}")

    # -------------------------------------------------------------
    # 💾 Save model
    # -------------------------------------------------------------
    joblib.dump(model, model_path)
    print(f"💾 Model saved at: {model_path}")


if __name__ == "__main__":
    retrain_pattern_model()
