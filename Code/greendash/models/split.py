import pandas as pd
from sklearn.model_selection import train_test_split
import json
import os

def create_splits():
    features_path = os.path.join(os.path.dirname(__file__), '../../data/features/features.parquet')
    df = pd.read_parquet(features_path)
    
    # Verify no age/income/postcode
    for col in ['age', 'income', 'postcode']:
        if col in df.columns:
            raise ValueError(f"Leakage/bias detected: {col} found in features!")
            
    # Check if 'is_persona' is present. If so, exclude them from splits
    if 'is_persona' in df.columns:
        persona_df = df[df['is_persona'] == True]
        df = df[df['is_persona'] != True]
    else:
        persona_df = pd.DataFrame()
        
    # We want a single split that we use for all models. We can stratify on an "any_take_up" flag
    # if available, or just random customer split. The guide says: "stratified by any-take-up".
    target_cols = [c for c in df.columns if c.startswith('take_up_')]
    if target_cols:
        df['any_take_up'] = df[target_cols].sum(axis=1) > 0
    else:
        df['any_take_up'] = 0
        
    customers = df[['customer_id', 'any_take_up']].drop_duplicates()
    
    # 70/15/15 split
    train_cust, temp_cust = train_test_split(
        customers['customer_id'], 
        test_size=0.3, 
        stratify=customers['any_take_up'], 
        random_state=42
    )
    
    temp_df = customers[customers['customer_id'].isin(temp_cust)]
    val_cust, test_cust = train_test_split(
        temp_df['customer_id'], 
        test_size=0.5, 
        stratify=temp_df['any_take_up'], 
        random_state=42
    )
    
    # Overlap assertion
    s_train = set(train_cust)
    s_val = set(val_cust)
    s_test = set(test_cust)
    
    assert len(s_train.intersection(s_val)) == 0
    assert len(s_train.intersection(s_test)) == 0
    assert len(s_val.intersection(s_test)) == 0
    
    splits = {
        'train': list(s_train),
        'val': list(s_val),
        'test': list(s_test),
        'personas': list(persona_df['customer_id']) if not persona_df.empty else []
    }
    
    out_dir = os.path.join(os.path.dirname(__file__), '../../data/splits')
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'splits.json'), 'w') as f:
        json.dump(splits, f)
        
    print(f"Splits generated: {len(s_train)} train, {len(s_val)} val, {len(s_test)} test.")
    
if __name__ == "__main__":
    create_splits()
