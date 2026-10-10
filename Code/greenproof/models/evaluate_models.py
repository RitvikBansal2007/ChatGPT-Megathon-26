from greenproof.models.utils import load_data, get_features_and_targets
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
import skops.io as sio
import numpy as np
import pandas as pd
import json
import os

def load_calibrator(target):
    calib_path = os.path.join(os.path.dirname(__file__), f'../../data/calibration/{target}_calibration.json')
    with open(calib_path, 'r') as f:
        breakpoints = json.load(f)
    
    xs = [bp['raw_score'] for bp in breakpoints]
    ys = [bp['calibrated_prob'] for bp in breakpoints]
    
    def calibrate(raw_scores):
        return np.interp(raw_scores, xs, ys)
        
    return calibrate

def compute_ece(y_true, y_prob, n_bins=10):
    bins = np.linspace(0., 1., n_bins + 1)
    binids = np.digitize(y_prob, bins) - 1
    
    bin_sums = np.bincount(binids, weights=y_prob, minlength=len(bins))
    bin_true = np.bincount(binids, weights=y_true, minlength=len(bins))
    bin_total = np.bincount(binids, minlength=len(bins))
    
    nonzero = bin_total != 0
    prob_true = bin_true[nonzero] / bin_total[nonzero]
    prob_pred = bin_sums[nonzero] / bin_total[nonzero]
    
    ece = np.sum(np.abs(prob_true - prob_pred) * (bin_total[nonzero] / len(y_true)))
    return ece

def lift_at_k(y_true, y_prob, k=0.10):
    order = np.argsort(y_prob)[::-1]
    y_true_sorted = y_true.values[order] if hasattr(y_true, 'values') else y_true[order]
    
    n_k = int(len(y_true) * k)
    if n_k == 0:
        return 0.0
        
    lift = y_true_sorted[:n_k].mean() / y_true.mean()
    return lift

def evaluate():
    _, _, test_df = load_data()
    X_test, Y_test = get_features_and_targets(test_df)
    
    models_dir = os.path.join(os.path.dirname(__file__), '../../data/models')
    
    print("--- MODEL EVALUATION (Test Set) ---")
    
    for target in Y_test.columns:
        model_path = os.path.join(models_dir, f'{target}_lgb.skops')
        untrusted = sio.get_untrusted_types(file=model_path)
        clf = sio.load(model_path, trusted=untrusted)
        calibrator = load_calibrator(target)
        
        raw_preds = clf.predict_proba(X_test)[:, 1]
        calib_preds = calibrator(raw_preds)
        
        y_true = Y_test[target]
        
        roc_auc = roc_auc_score(y_true, calib_preds)
        pr_auc = average_precision_score(y_true, calib_preds)
        brier = brier_score_loss(y_true, calib_preds)
        ece = compute_ece(y_true, calib_preds)
        lift = lift_at_k(y_true, calib_preds, k=0.10)
        
        print(f"\n{target}:")
        print(f"  ROC-AUC:   {roc_auc:.4f}")
        print(f"  PR-AUC:    {pr_auc:.4f}")
        print(f"  Brier:     {brier:.4f}")
        print(f"  ECE:       {ece:.4f}")
        print(f"  Lift@10%:  {lift:.2f}x")
        
        # Placebo test (shuffle labels)
        shuffled_y = np.random.permutation(y_true)
        placebo_auc = roc_auc_score(shuffled_y, calib_preds)
        print(f"  Placebo AUC: {placebo_auc:.4f} (should be ~0.50)")
        
        if roc_auc > 0.95:
            print("  ⚠️ WARNING: AUC > 0.95. Possible leakage!")

if __name__ == "__main__":
    evaluate()
