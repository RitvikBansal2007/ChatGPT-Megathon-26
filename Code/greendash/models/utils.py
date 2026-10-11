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
    # Drop datetime columns and complex types (lists/dicts)
    df = df.select_dtypes(exclude=['datetime', 'datetime64[ns]'])
    
    # Drop list/array columns which can't be converted to category
    drop_cols = [c for c in df.columns if 'conflict' in c or 'critical_missing' in c]
    df = df.drop(columns=drop_cols, errors='ignore')
    
    target_cols = [c for c in df.columns if c.startswith('take_up_')]
    # customer_key is a row number: an identifier must never be a model input
    feature_cols = [c for c in df.columns if c not in target_cols and c not in ['customer_id', 'customer_key', 'is_persona']]
    
    # Cast object/string columns to category for LightGBM
    for c in feature_cols:
        if df[c].dtype == 'object' or df[c].dtype == 'string':
            df[c] = df[c].astype('category')
                
    return df[feature_cols], df[target_cols]
