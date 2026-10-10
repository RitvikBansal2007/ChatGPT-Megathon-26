import pandas as pd
import json
import os

def load_data():
    features_path = os.path.join(os.path.dirname(__file__), '../../data/features/features.parquet')
    splits_path = os.path.join(os.path.dirname(__file__), '../../data/splits/splits.json')
    
    df = pd.read_parquet(features_path)
    with open(splits_path, 'r') as f:
        splits = json.load(f)
        
    train_df = df[df['customer_id'].isin(splits['train'])]
    val_df = df[df['customer_id'].isin(splits['val'])]
    test_df = df[df['customer_id'].isin(splits['test'])]
    
    return train_df, val_df, test_df

def get_features_and_targets(df):
    target_cols = [c for c in df.columns if c.startswith('take_up_')]
    feature_cols = [c for c in df.columns if c not in target_cols and c not in ['customer_id', 'is_persona']]
    return df[feature_cols], df[target_cols]
