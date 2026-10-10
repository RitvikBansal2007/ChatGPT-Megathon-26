import pandas as pd
import numpy as np
import hashlib
import json
import skops.io as sio
import os
from greenproof.models.utils import load_data, get_features_and_targets
from greenproof.models.evaluate_models import load_calibrator

MODELS_DIR = os.path.join(os.path.dirname(__file__), '../../data/models')

def verify_hash(model_filename):
    hash_path = os.path.join(MODELS_DIR, 'hashes.json')
    if not os.path.exists(hash_path):
        raise Exception("Security Error: hashes.json not found")
        
    with open(hash_path, 'r') as f:
        hashes = json.load(f)
        
    if model_filename not in hashes:
        raise Exception(f"Security Error: Hash for {model_filename} not in hashes.json")
        
    model_path = os.path.join(MODELS_DIR, model_filename)
    with open(model_path, 'rb') as f:
        computed_hash = hashlib.sha256(f.read()).hexdigest()
        
    if computed_hash != hashes[model_filename]:
        raise Exception(f"Security Error: Hash mismatch for {model_filename}! Model compromised.")

def load_verified_model(target):
    filename = f'{target}_lgb.skops'
    verify_hash(filename)
    model_path = os.path.join(MODELS_DIR, filename)
    untrusted = sio.get_untrusted_types(file=model_path)
    return sio.load(model_path, trusted=untrusted)

def score_customers(customer_ids):
    # Load full feature dataset
    features_path = os.path.join(os.path.dirname(__file__), '../../data/features/features.parquet')
    df = pd.read_parquet(features_path)
    
    # Filter for requested customers
    df_subset = df[df['customer_id'].isin(customer_ids)].copy()
    if df_subset.empty:
        print("No matching customers found.")
        return None
        
    X, _ = get_features_and_targets(df_subset)
    
    targets = ['take_up_GP01', 'take_up_GP02', 'take_up_GP03', 'take_up_GP04']
    scores = {}
    
    for target in targets:
        model = load_verified_model(target)
        calibrator = load_calibrator(target)
        
        raw_preds = model.predict_proba(X)[:, 1]
        calib_preds = calibrator(raw_preds)
        scores[target] = calib_preds
        df_subset[f'score_{target}'] = calib_preds
        
    # Pick top product to recommend
    # We find the argmax across the 4 scores
    score_cols = [f'score_{t}' for t in targets]
    df_subset['RECOMMEND'] = df_subset[score_cols].idxmax(axis=1).str.replace('score_', '')
    df_subset['RECOMMEND_SCORE'] = df_subset[score_cols].max(axis=1)
    
    return df_subset[['customer_id', 'RECOMMEND', 'RECOMMEND_SCORE'] + score_cols]

def main():
    _, _, test_df = load_data()
    test_cust_ids = test_df['customer_id'].unique()
    
    print(f"Scoring {len(test_cust_ids)} test customers...")
    results = score_customers(test_cust_ids)
    
    out_path = os.path.join(os.path.dirname(__file__), '../../data/test_predictions.csv')
    results.to_csv(out_path, index=False)
    print(f"Predictions saved to {out_path}")
    
    print("\nRECOMMEND share per product (Test Set):")
    print(results['RECOMMEND'].value_counts(normalize=True) * 100)
    
    # Score Personas
    splits_path = os.path.join(os.path.dirname(__file__), '../../data/splits/splits.json')
    with open(splits_path, 'r') as f:
        splits = json.load(f)
        
    if splits.get('personas'):
        print(f"\nScoring {len(splits['personas'])} personas...")
        persona_results = score_customers(splits['personas'])
        print(persona_results[['customer_id', 'RECOMMEND', 'RECOMMEND_SCORE']])
    else:
        print("\nNo personas found in splits to score.")

if __name__ == "__main__":
    main()
