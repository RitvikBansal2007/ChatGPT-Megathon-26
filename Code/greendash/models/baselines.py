from greendash.models.utils import load_data, get_features_and_targets
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import pandas as pd
import numpy as np

def train_baselines():
    train_df, val_df, test_df = load_data()
    X_train, Y_train = get_features_and_targets(train_df)
    X_val, Y_val = get_features_and_targets(val_df)
    
    # Simple rule heuristics based on dataset logic
    heuristics = {
        'take_up_GP01': lambda df: df['fuel_spend_last_6m'] / df['fuel_spend_last_6m'].max(),
        'take_up_GP02': lambda df: df['gas_kwh_last_year'] / df['gas_kwh_last_year'].max(),
        'take_up_GP03': lambda df: df['electricity_kwh_last_year'] / df['electricity_kwh_last_year'].max(),
        'take_up_GP04': lambda df: df['paper_statements']
    }
    
    print("--- BASELINE RESULTS (Validation Set) ---")
    
    for target in Y_train.columns:
        print(f"\nTarget: {target}")
        
        # Logistic Regression Baseline
        clf = LogisticRegression(max_iter=1000)
        clf.fit(X_train, Y_train[target])
        lr_preds = clf.predict_proba(X_val)[:, 1]
        
        lr_auc = roc_auc_score(Y_val[target], lr_preds)
        print(f"  Logistic Regression AUC: {lr_auc:.4f}")
        
        # Heuristic Baseline
        if target in heuristics:
            h_preds = heuristics[target](X_val)
            # handle NaNs if any
            h_preds = h_preds.fillna(0)
            h_auc = roc_auc_score(Y_val[target], h_preds)
            print(f"  Rule Heuristic AUC:      {h_auc:.4f}")

if __name__ == "__main__":
    train_baselines()
