from greendash.models.utils import load_data, get_features_and_targets
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

def evaluate(save_summary=True):
    from greendash.models.baselines import train_baselines
    
    _, _, test_df = load_data()
    X_test, Y_test = get_features_and_targets(test_df)
    
    models_dir = os.path.join(os.path.dirname(__file__), '../../data/models')
    
    print("--- MODEL EVALUATION (Test Set) ---")
    
    baseline_metrics = train_baselines(use_test=True)
    
    baselines_output = {}
    all_calib_preds = []
    all_y_true = []
    
    for target in Y_test.columns:
        model_path = os.path.join(models_dir, f'{target}_lgb.skops')
        untrusted = sio.get_untrusted_types(file=model_path)
        clf = sio.load(model_path, trusted=untrusted)
        calibrator = load_calibrator(target)
        
        raw_preds = clf.predict_proba(X_test)[:, 1]
        calib_preds = calibrator(raw_preds)
        
        y_true = Y_test[target]
        all_calib_preds.extend(calib_preds)
        all_y_true.extend(y_true.values)
        
        roc_auc = float(roc_auc_score(y_true, calib_preds))
        pr_auc = float(average_precision_score(y_true, calib_preds))
        brier = float(brier_score_loss(y_true, calib_preds))
        ece = float(compute_ece(y_true, calib_preds))
        lift = float(lift_at_k(y_true, calib_preds, k=0.10))
        
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
            
        pid = target.replace("take_up_", "")
        bl = baseline_metrics.get(pid, {})
        baselines_output[pid] = {
            "lgbm_auc": round(roc_auc, 3),
            "lgbm_pr_auc": round(pr_auc, 3),
            "lgbm_brier": round(brier, 4),
            "lgbm_ece": round(ece, 4),
            "lgbm_lift_top10": round(lift, 2),
            "base_rate": round(float(y_true.mean()), 4),
            **bl
        }
        
    all_calib_preds = np.array(all_calib_preds)
    all_y_true = np.array(all_y_true)
    
    # Calibration bins
    bins = [(0.0, 0.10, '0–10%'), (0.10, 0.20, '10–20%'), (0.20, 0.40, '20–40%'), 
            (0.40, 0.60, '40–60%'), (0.60, 0.80, '60–80%'), (0.80, 1.001, '80–100%')]
    calib_summary = []
    for low, high, label in bins:
        mask = (all_calib_preds >= low) & (all_calib_preds < high)
        if np.sum(mask) > 0:
            mean_pred = float(np.mean(all_calib_preds[mask]))
            mean_actual = float(np.mean(all_y_true[mask]))
        else:
            continue  # no predictions in this bin: report nothing rather than a made-up point
        calib_summary.append({'bin': label, 'n': int(np.sum(mask)), 'mean_pred': round(mean_pred, 3), 'mean_actual': round(mean_actual, 3)})
        
    # Terciles
    t_low, t_high = np.percentile(all_calib_preds, [33.3, 66.7])
    low_mask = all_calib_preds <= t_low
    mid_mask = (all_calib_preds > t_low) & (all_calib_preds <= t_high)
    high_mask = all_calib_preds > t_high
    brier_terciles = {
        'low': round(float(brier_score_loss(all_y_true[low_mask], all_calib_preds[low_mask])), 4),
        'mid': round(float(brier_score_loss(all_y_true[mid_mask], all_calib_preds[mid_mask])), 4),
        'high': round(float(brier_score_loss(all_y_true[high_mask], all_calib_preds[high_mask])), 4)
    }
    
    # Scenarios: a suite that does not run is reported as not run, never as passed
    try:
        from eval.scenarios.runner import run_all
        scen_results = run_all(write=True)
        passed = sum(1 for r in scen_results if r["passed"])
        total = len(scen_results)
        failures = [f"{r['id']}: {', '.join(r['failures'])}" for r in scen_results if not r["passed"]]
    except Exception as e:
        passed, total, failures = 0, 0, [f"suite did not run: {type(e).__name__}: {e}"]

    # Categoriser: 5-fold GroupKFold on unseen merchants
    try:
        from greendash.categoriser.evaluate import evaluate as evaluate_categoriser
        rules_f1, cat_f1 = (round(v, 3) for v in evaluate_categoriser())
    except Exception as e:
        print("Categoriser evaluation did not run:", e)
        rules_f1 = cat_f1 = None

    # Explanations: counted from the judge output, nothing assumed
    llm_eval = {"evaluated": 0}
    judge_path = os.path.join(os.path.dirname(__file__), '../../out/judge_evaluation_results.json')
    if os.path.exists(judge_path):
        with open(judge_path) as f:
            judged = json.load(f)
        n = len(judged)
        if n:
            llm_eval = {
                "evaluated": n,
                "template_fallback_rate": round(sum(j["explanation"].get("source") == "template" for j in judged) / n, 3),
                "judged_by_model": sum(j["evaluation"].get("judge") == "llm" for j in judged),
                "written_by_model": sum(j["explanation"].get("source") == "llm" for j in judged),
                "fallback_reasons": dict(sorted(__import__("collections").Counter(
                    j["explanation"].get("fallback_reason") or "NONE" for j in judged
                    if j["explanation"].get("source") != "llm").items())),
                "faithfulness": round(sum(j["evaluation"].get("faithfulness", 0) for j in judged) / n, 3),
                "canary_leakage_rate": round(sum(j["evaluation"].get("canary_leakage", 0) for j in judged) / n, 3),
            }

    with open(os.path.join(os.path.dirname(__file__), '../../data/splits/splits.json')) as f:
        split_sizes = {k: len(v) for k, v in json.load(f).items()}

    eval_summary = {
        "as_of": "30 Jun 2026",
        "synthetic": True,
        "measured": True,
        "split": split_sizes,
        "baselines": baselines_output,
        "calibration": calib_summary,
        "brier_by_tercile": brier_terciles,
        "llm_eval": llm_eval,
        "scenarios": {"passed": passed, "total": total, "failures": failures},
        "categoriser": {"macro_f1": cat_f1, "rules_only_f1": rules_f1}
    }

    if save_summary:
        out_path = os.path.join(os.path.dirname(__file__), '../../out/eval_summary.json')
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w') as f:
            json.dump(eval_summary, f, indent=2)
        print(f"\nSaved real evaluation summary to: {out_path}")
        
        try:
            from eval.report import generate_report
            generate_report()
        except Exception as e:
            print("Failed to regenerate report:", e)
            
    return eval_summary

if __name__ == "__main__":
    evaluate()
