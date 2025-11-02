import pandas as pd
import os

def fix_corrupted_csv(file_path):
    """
    Fix corrupted CSV files by reading line by line and writing valid lines.
    """
    try:
        # Read the file line by line
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        if len(lines) <= 1:
            print(f"File {file_path} has no data to fix")
            return
            
        # Expected header
        header = lines[0].strip()
        expected_columns = len(header.split(','))
        
        valid_lines = [header + '\n']  # Start with header
        
        for i, line in enumerate(lines[1:], 1):  # Skip header
            # Skip empty lines
            if not line.strip():
                continue
                
            # Check if line has expected number of fields
            fields = line.strip().split(',')
            if len(fields) == expected_columns:
                valid_lines.append(line)
            else:
                print(f"⚠️ Skipping corrupted line {i+1}: {line[:50]}...")
        
        # Write valid lines back to file
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            f.writelines(valid_lines)
            
        print(f"✅ Fixed CSV file: {len(lines)} → {len(valid_lines)} valid lines")
        
        # Verify with pandas
        df = pd.read_csv(file_path)
        print(f"📊 Final count: {len(df)} records")
        
    except Exception as e:
        print(f"❌ Error fixing CSV file: {e}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Fix behavior feedback
    behavior_path = os.path.join(base_dir, "data", "behavior_feedback.csv")
    if os.path.exists(behavior_path):
        print(f"🔧 Fixing {behavior_path}")
        fix_corrupted_csv(behavior_path)
    
    # Fix pattern feedback
    pattern_path = os.path.join(base_dir, "data", "pattern_feedback.csv")
    if os.path.exists(pattern_path):
        print(f"🔧 Fixing {pattern_path}")
        fix_corrupted_csv(pattern_path)
        
    print("✅ CSV fix complete!")