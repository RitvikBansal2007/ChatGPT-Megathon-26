import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import skops.io as sio
import os
import json
from greendash.models.utils import load_data, get_features_and_targets
from greendash.models.score import load_verified_model

class ConfidenceCalculator:
    def __init__(self):
        self.iso_forests = {}
        
    def fit(self, X_train):
        print("Fitting Isolation Forest for in-distribution check...")
        self.iso_forest = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        # handle missing values for IsolationForest
        X_imputed = X_train.fillna(X_train.median())
        self.iso_forest.fit(X_imputed)
        print("Done.")

    def compute_completeness(self, X):
        # Score 0.25 if >90% complete, 0.125 if >70%, else 0
        non_null_frac = 1.0 - (X.isnull().sum(axis=1) / X.shape[1])
        scores = np.where(non_null_frac > 0.9, 0.25, np.where(non_null_frac > 0.7, 0.125, 0.0))
        return scores
        
    def compute_recency(self, X):
        # We assume recency is good if they have >0 fuel_spend_last_6m or gas_kwh_last_year
        # based on whatever features we have
        # Simplification: If sum of numeric features > threshold, they are active
        active = (X.fillna(0).abs().sum(axis=1) > 10)
        return np.where(active, 0.25, 0.0)
        
    def compute_stability(self, model, X):
        # LGBM isn't a random forest, but we can approximate stability by 
        # predicting with different tree limits (e.g. 20, 40, 60, 80, 100)
        # This acts as our "5 bootstraps" proxy without retraining 5 models.
        preds = []
        for limit in [20, 40, 60, 80, 100]:
            preds.append(model.predict_proba(X, num_iteration=limit)[:, 1])
            
        preds = np.array(preds)
        variance = np.var(preds, axis=0)
        # Score 0.25 if variance is low (<0.01), else 0
        return np.where(variance < 0.01, 0.25, 0.0)
        
    def compute_in_distribution(self, X):
        X_imputed = X.fillna(X.median())
        is_inlier = self.iso_forest.predict(X_imputed)
        # IsolationForest returns 1 for inlier, -1 for outlier
        return np.where(is_inlier == 1, 0.25, 0.0)
        
    def get_confidence_score(self, target, X):
        model = load_verified_model(target)
        
        c1 = self.compute_completeness(X)
        c2 = self.compute_recency(X)
        c3 = self.compute_stability(model, X)
        c4 = self.compute_in_distribution(X)
        
        total = c1 + c2 + c3 + c4
        return total

def validate_confidence():
    train_df, val_df, _ = load_data()
    X_train, _ = get_features_and_targets(train_df)
    X_val, Y_val = get_features_and_targets(val_df)
    
    calc = ConfidenceCalculator()
    calc.fit(X_train)
    
    out_dir = os.path.join(os.path.dirname(__file__), '../../data/metrics')
    os.makedirs(out_dir, exist_ok=True)
    
    results = {}
    for target in Y_val.columns:
        print(f"Validating confidence for {target}...")
        conf_scores = calc.get_confidence_score(target, X_val)
        
        # Calculate Brier score for high vs low confidence
        model = load_verified_model(target)
        preds = model.predict_proba(X_val)[:, 1]
        
        from sklearn.metrics import brier_score_loss
        
        high_conf_mask = conf_scores >= 0.75
        low_conf_mask = conf_scores < 0.75
        
        brier_high = brier_score_loss(Y_val[target][high_conf_mask], preds[high_conf_mask]) if high_conf_mask.sum() > 0 else None
        brier_low = brier_score_loss(Y_val[target][low_conf_mask], preds[low_conf_mask]) if low_conf_mask.sum() > 0 else None
        
        results[target] = {
            "brier_high_confidence": float(brier_high) if brier_high is not None else None,
            "brier_low_confidence": float(brier_low) if brier_low is not None else None,
            "correlation_with_propensity": float(np.corrcoef(conf_scores, preds)[0, 1])
        }
        
    out_path = os.path.join(out_dir, 'confidence_validation.json')
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"Validation saved to {out_path}")

if __name__ == "__main__":
    validate_confidence()
