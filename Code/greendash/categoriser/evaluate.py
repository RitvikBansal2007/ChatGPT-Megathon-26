import pandas as pd
import numpy as np
from sklearn.model_selection import GroupKFold
from sklearn.metrics import f1_score
from greendash.categoriser.rules import categorize_batch
from greendash.categoriser.model import build_pipeline
import os

def clean_for_grouping(text):
    import re
    # Remove digits and common prefixes to group similar merchants
    text = re.sub(r'\d+', '', text.lower())
    text = re.sub(r'^(pos|vis|dd|card payment to|paypal \*)\s*', '', text)
    return text.strip()

def evaluate():
    data_path = os.path.join(os.path.dirname(__file__), '../../data/raw/transactions.parquet')
    df = pd.read_parquet(data_path)
    
    # We only care about evaluation, let's use a subset if it's too big, 
    # but the instructions say train on 20k rows so it's fine to use all.
    df['merchant_group'] = df['merchant_description'].apply(clean_for_grouping)
    
    # GroupKFold to test unseen merchants
    gkf = GroupKFold(n_splits=5)
    
    X = df['merchant_description'].values
    y = df['true_category'].values
    groups = df['merchant_group'].values
    
    rules_f1s = []
    combined_f1s = []
    
    for train_idx, test_idx in gkf.split(X, y, groups):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Rules only
        rules_preds = categorize_batch(X_test)
        rules_f1s.append(f1_score(y_test, rules_preds, average='macro'))
        
        # Train ML model
        pipeline = build_pipeline()
        pipeline.fit(X_train, y_train)
        ml_preds = pipeline.predict(X_test)
        
        # Combined: rules first, then ML if rules returns "Other"
        combined_preds = []
        for r_pred, m_pred in zip(rules_preds, ml_preds):
            if r_pred != "Other":
                combined_preds.append(r_pred)
            else:
                combined_preds.append(m_pred)
                
        combined_f1s.append(f1_score(y_test, combined_preds, average='macro'))
        
    print(f"Rules-only Macro-F1 (unseen merchants): {np.mean(rules_f1s):.4f}")
    print(f"Rules+ML Macro-F1 (unseen merchants): {np.mean(combined_f1s):.4f}")

if __name__ == "__main__":
    evaluate()
