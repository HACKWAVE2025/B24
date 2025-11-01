import pandas as pd
import os

# Auto-detect correct CSV path
base_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(base_dir, "data", "behavior_dataset.csv")

print(f"📂 Looking for dataset at: {data_path}")

if not os.path.exists(data_path):
    print("❌ Dataset not found!")
    exit()

df = pd.read_csv(data_path)
print("Before:", df.shape, list(df.columns))

# Add missing columns with default values
if 'day_of_week' not in df.columns:
    df['day_of_week'] = 2  # e.g., Tuesday default
if 'delta_hours' not in df.columns:
    df['delta_hours'] = 24.0  # e.g., default 1-day gap

# Drop label column if it's not needed
if 'label' in df.columns:
    df = df.drop(columns=['label'])

df.to_csv(data_path, index=False)
print("✅ Updated CSV saved with columns:", list(df.columns))
