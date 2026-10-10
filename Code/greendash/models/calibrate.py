from greendash.models.utils import load_data, get_features_and_targets
from sklearn.isotonic import IsotonicRegression
import skops.io as sio
import pandas as pd
import numpy as np
import json
import os

def calibrate_models():
    _, val_df, _ = load_data()
    X_val, Y_val = get_features_and_targets(val_df)
    
    models_dir = os.path.join(os.path.dirname(__file__), '../../data/models')
    out_dir = os.path.join(os.path.dirname(__file__), '../../data/calibration')
    os.makedirs(out_dir, exist_ok=True)
    
    for target in Y_val.columns:
        model_path = os.path.join(models_dir, f'{target}_lgb.skops')
        untrusted = sio.get_untrusted_types(file=model_path)
        clf = sio.load(model_path, trusted=untrusted)
        
        # Predict on validation
        val_preds = clf.predict_proba(X_val)[:, 1]
        
        # Fit Isotonic Regression
        iso = IsotonicRegression(out_of_bounds='clip')
        iso.fit(val_preds, Y_val[target])
        
        # Extract breakpoints
        breakpoints = []
        for x, y in zip(iso.X_thresholds_, iso.y_thresholds_):
            breakpoints.append({"raw_score": float(x), "calibrated_prob": float(y)})
            
        json_path = os.path.join(out_dir, f'{target}_calibration.json')
        with open(json_path, 'w') as f:
            json.dump(breakpoints, f, indent=2)
            
        print(f"Saved calibration JSON for {target} to {json_path}")

if __name__ == "__main__":
    calibrate_models()
