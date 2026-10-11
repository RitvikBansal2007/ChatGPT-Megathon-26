from greendash.models.utils import load_data, get_features_and_targets
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score
import pandas as pd
import numpy as np

def train_baselines(use_test=True):
    train_df, val_df, test_df = load_data()
    X_train, Y_train = get_features_and_targets(train_df)
    eval_df = test_df if use_test else val_df
    X_eval, Y_eval = get_features_and_targets(eval_df)
    
    X_train_enc = pd.get_dummies(X_train, drop_first=True).fillna(0)
    X_eval_enc = pd.get_dummies(X_eval, drop_first=True).fillna(0)
    X_train_enc, X_eval_enc = X_train_enc.align(X_eval_enc, join='left', axis=1, fill_value=0)
    
    heuristics = {
        'take_up_GP01': lambda df: df['avg_monthly_fuel_gbp'].fillna(0) if 'avg_monthly_fuel_gbp' in df else df.get('annual_mileage', pd.Series(0, index=df.index)).fillna(0),
        'take_up_GP02': lambda df: df.get('gas_kwh_12m', pd.Series(0, index=df.index)).fillna(0),
        'take_up_GP03': lambda df: df.get('electricity_kwh_12m', pd.Series(0, index=df.index)).fillna(0),
        'take_up_GP04': lambda df: df.get('paper_statements_12m', pd.Series(0, index=df.index)).fillna(0)
    }
    
    split_name = "Test Set" if use_test else "Validation Set"
    print(f"--- BASELINE RESULTS ({split_name}) ---")
    
    results = {}
    for target in Y_train.columns:
        print(f"\nTarget: {target}")
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
        clf.fit(X_train_enc, Y_train[target])
        lr_preds = clf.predict_proba(X_eval_enc)[:, 1]
        
        lr_auc = float(roc_auc_score(Y_eval[target], lr_preds))
        print(f"  Logistic Regression AUC: {lr_auc:.4f}")
        
        h_auc = 0.5
        if target in heuristics:
            h_preds = heuristics[target](X_eval)
            h_preds = h_preds.fillna(0)
            if len(np.unique(h_preds)) > 1:
                h_auc = float(roc_auc_score(Y_eval[target], h_preds))
            print(f"  Rule Heuristic AUC:      {h_auc:.4f}")
            
        pid = target.replace("take_up_", "")
        results[pid] = {
            "lr_auc": round(lr_auc, 3),
            "rule_auc": round(h_auc, 3)
        }
        
    return results

if __name__ == "__main__":
    train_baselines()

