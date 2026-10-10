import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import skops.io as sio
from sklearn.metrics import roc_curve, precision_recall_curve, auc
from sklearn.calibration import calibration_curve
import shap
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from greendash.models.utils import load_data, get_features_and_targets
from greendash.models.evaluate_models import load_calibrator

def plot_all(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    _, _, test_df = load_data()
    X_test, Y_test = get_features_and_targets(test_df)
    models_dir = os.path.join(os.path.dirname(__file__), '../data/models')

    plt.figure(figsize=(10, 8))
    for target in Y_test.columns:
        model_path = os.path.join(models_dir, f'{target}_lgb.skops')
        untrusted = sio.get_untrusted_types(file=model_path)
        clf = sio.load(model_path, trusted=untrusted)
        calibrator = load_calibrator(target)
        
        raw_preds = clf.predict_proba(X_test)[:, 1]
        calib_preds = calibrator(raw_preds)
        y_true = Y_test[target]
        
        # ROC
        fpr, tpr, _ = roc_curve(y_true, calib_preds)
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, label=f'{target} (AUC = {roc_auc:.2f})')

    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curves')
    plt.legend()
    plt.savefig(os.path.join(output_dir, 'roc_curves.png'))
    plt.close()

    plt.figure(figsize=(10, 8))
    for target in Y_test.columns:
        model_path = os.path.join(models_dir, f'{target}_lgb.skops')
        untrusted = sio.get_untrusted_types(file=model_path)
        clf = sio.load(model_path, trusted=untrusted)
        calibrator = load_calibrator(target)
        raw_preds = clf.predict_proba(X_test)[:, 1]
        calib_preds = calibrator(raw_preds)
        y_true = Y_test[target]
        
        # PR
        p, r, _ = precision_recall_curve(y_true, calib_preds)
        pr_auc = auc(r, p)
        plt.plot(r, p, label=f'{target} (AUC = {pr_auc:.2f})')

    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curves')
    plt.legend()
    plt.savefig(os.path.join(output_dir, 'pr_curves.png'))
    plt.close()

    plt.figure(figsize=(10, 8))
    for target in Y_test.columns:
        model_path = os.path.join(models_dir, f'{target}_lgb.skops')
        untrusted = sio.get_untrusted_types(file=model_path)
        clf = sio.load(model_path, trusted=untrusted)
        calibrator = load_calibrator(target)
        raw_preds = clf.predict_proba(X_test)[:, 1]
        calib_preds = calibrator(raw_preds)
        y_true = Y_test[target]
        
        prob_true, prob_pred = calibration_curve(y_true, calib_preds, n_bins=10)
        plt.plot(prob_pred, prob_true, marker='o', label=f'{target}')

    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel('Mean predicted probability')
    plt.ylabel('Fraction of positives')
    plt.title('Calibration Curves')
    plt.legend()
    plt.savefig(os.path.join(output_dir, 'calibration_curves.png'))
    plt.close()

    # SHAP for the first target as an example (or all if requested, but let's do all)
    for target in Y_test.columns:
        model_path = os.path.join(models_dir, f'{target}_lgb.skops')
        untrusted = sio.get_untrusted_types(file=model_path)
        clf = sio.load(model_path, trusted=untrusted)
        
        # Using tree explainer on LightGBM
        explainer = shap.TreeExplainer(clf)
        shap_values = explainer.shap_values(X_test)
        
        # Binary classification usually returns a list of [negative_class, positive_class] or just a single array
        if isinstance(shap_values, list):
            sv = shap_values[1]
        else:
            sv = shap_values
            
        plt.figure(figsize=(10, 8))
        shap.summary_plot(sv, X_test, show=False)
        plt.savefig(os.path.join(output_dir, f'shap_{target}.png'))
        plt.close()

if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else 'out/plots'
    plot_all(out_dir)
