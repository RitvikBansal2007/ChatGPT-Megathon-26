import pandas as pd
import numpy as np
import shap
import skops.io as sio
import os
import json
from greendash.models.utils import load_data, get_features_and_targets
from greendash.models.score import load_verified_model

def compute_reasons():
    train_df, _, test_df = load_data()
    X_train, _ = get_features_and_targets(train_df)
    X_test, Y_test = get_features_and_targets(test_df)
    
    out_dir = os.path.join(os.path.dirname(__file__), '../../data/metrics')
    os.makedirs(out_dir, exist_ok=True)
    
    reasons_out = {}
    
    for target in Y_test.columns:
        print(f"Computing reasons for {target}...")
        model = load_verified_model(target)
        
        # Explain using TreeExplainer
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)
        
        # If binary classification, shap_values is a list of arrays (one for each class). We want the positive class (index 1)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
            
        # We process the first 5 customers in the test set to output sample reasons
        target_reasons = []
        for i in range(5):
            cust_id = test_df.iloc[i]['customer_id']
            shaps = shap_values[i]
            features = X_test.iloc[i]
            
            # Get top positive and negative features
            top_pos_idx = np.argsort(shaps)[-3:][::-1]
            top_neg_idx = np.argsort(shaps)[:3]
            
            from datetime import date
            pos_reasons = []
            for idx in top_pos_idx:
                if shaps[idx] > 0:
                    feat_name = X_test.columns[idx]
                    feat_val = features.iloc[idx]
                    code_val = f"HIGH_{feat_name.upper()}" if feat_val > X_train[feat_name].median() else f"LOW_{feat_name.upper()}"
                    pos_reasons.append({
                        "code": code_val,
                        "phrase": f"{code_val.replace('_', ' ').title()} recorded",
                        "metric": feat_name,
                        "value": float(feat_val),
                        "display": str(float(feat_val)),
                        "observed_at": str(date.today()),
                        "source": "inferred_transactions"
                    })
                    
            neg_reasons = []
            for idx in top_neg_idx:
                if shaps[idx] < 0:
                    feat_name = X_test.columns[idx]
                    feat_val = features.iloc[idx]
                    code_val = f"HIGH_{feat_name.upper()}" if feat_val > X_train[feat_name].median() else f"LOW_{feat_name.upper()}"
                    neg_reasons.append({
                        "code": code_val,
                        "phrase": f"{code_val.replace('_', ' ').title()} recorded",
                        "metric": feat_name,
                        "value": float(feat_val),
                        "display": str(float(feat_val)),
                        "observed_at": str(date.today()),
                        "source": "inferred_transactions"
                    })
                    
            target_reasons.append({
                "customer_id": cust_id,
                "positive_drivers": pos_reasons,
                "negative_drivers": neg_reasons
            })
            
        reasons_out[target] = target_reasons
        
    out_path = os.path.join(out_dir, 'sample_reasons.json')
    with open(out_path, 'w') as f:
        json.dump(reasons_out, f, indent=2)
    print(f"Sample reasons saved to {out_path}")

if __name__ == "__main__":
    compute_reasons()
