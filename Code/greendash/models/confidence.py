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
        
    def _prep_features(self, X):
        X_df = X.copy()
        for col in X_df.columns:
            if X_df[col].dtype.name == "category" or X_df[col].dtype == object:
                X_df[col] = X_df[col].astype("category").cat.codes
            else:
                med = X_df[col].median()
                X_df[col] = X_df[col].fillna(med if not pd.isna(med) else 0.0)
        return X_df

    def fit(self, X_train):
        print("Fitting Isolation Forest for in-distribution check...")
        self.iso_forest = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        X_imputed = self._prep_features(X_train)
        self.iso_forest.fit(X_imputed)
        print("Done.")

    def compute_completeness(self, X):
        non_null_frac = 1.0 - (X.isnull().sum(axis=1) / X.shape[1])
        scores = np.where(non_null_frac > 0.9, 0.25, np.where(non_null_frac > 0.7, 0.15, 0.05))
        return scores
        
    def compute_recency(self, X):
        active = (self._prep_features(X).abs().sum(axis=1) > 10)
        return np.where(active, 0.25, 0.10)
        
    def compute_stability(self, model, X):
        X_m = X[[col for col in model.feature_name_ if col in X.columns]].copy()
        for col in ['epc_band', 'roof_suitability', 'vehicle_fuel_type']:
            if col in X_m.columns:
                X_m[col] = X_m[col].astype('category')
        preds = []
        for limit in [20, 40, 60, 80, 100]:
            preds.append(model.predict_proba(X_m, num_iteration=limit)[:, 1])
            
        preds = np.array(preds)
        variance = np.var(preds, axis=0)
        return np.where(variance < 0.005, 0.25, np.where(variance < 0.02, 0.15, 0.05))
        
    def compute_in_distribution(self, X):
        X_imputed = self._prep_features(X)
        is_inlier = self.iso_forest.predict(X_imputed)
        return np.where(is_inlier == 1, 0.25, 0.10)
        
    def get_confidence_score(self, target, X):
        model = load_verified_model(target)
        c1 = self.compute_completeness(X)
        c2 = self.compute_recency(X)
        c3 = self.compute_stability(model, X)
        c4 = self.compute_in_distribution(X)
        return c1 + c2 + c3 + c4

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
        
        model = load_verified_model(target)
        X_m = X_val[[col for col in model.feature_name_ if col in X_val.columns]].copy()
        for col in ['epc_band', 'roof_suitability', 'vehicle_fuel_type']:
            if col in X_m.columns:
                X_m[col] = X_m[col].astype('category')
        preds = model.predict_proba(X_m)[:, 1]
        
        from sklearn.metrics import brier_score_loss
        
        med = float(np.median(conf_scores))
        high_conf_mask = conf_scores >= med
        low_conf_mask = conf_scores < med
        if low_conf_mask.sum() == 0:
            low_conf_mask = conf_scores <= med
            high_conf_mask = conf_scores > med
        
        brier_high = brier_score_loss(Y_val[target][high_conf_mask], preds[high_conf_mask]) if high_conf_mask.sum() > 0 else None
        brier_low = brier_score_loss(Y_val[target][low_conf_mask], preds[low_conf_mask]) if low_conf_mask.sum() > 0 else None
        
        corr = float(np.corrcoef(conf_scores, preds)[0, 1]) if len(set(conf_scores)) > 1 else 0.0
        results[target] = {
            "brier_high_confidence": float(brier_high) if brier_high is not None else None,
            "brier_low_confidence": float(brier_low) if brier_low is not None else None,
            "correlation_with_propensity": corr
        }
        
    out_path = os.path.join(out_dir, 'confidence_validation.json')
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"Validation saved to {out_path}")

if __name__ == "__main__":
    validate_confidence()
