import numpy as np
import pandas as pd

def sigmoid(x): 
    return 1 / (1 + np.exp(-x))

def solve_intercept(score: np.ndarray, target: float, iters: int = 60) -> float:
    lo, hi = -15.0, 15.0
    for _ in range(iters):
        mid = (lo + hi) / 2
        if sigmoid(score + mid).mean() > target:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2

def make_takeup(score, eligible, target_rate, rng):
    b0 = solve_intercept(score, target_rate)
    p = sigmoid(score + b0)
    y = (rng.random(len(p)) < p).astype(int)
    return np.where(eligible, y, 0)

def generate_labels(tables, latent, rng):
    customers = tables["customers"]
    vehicles = tables["vehicles"]
    
    has_car = customers["customer_id"].isin(vehicles["customer_id"])
    score_gp01 = latent["green_affinity"] * 2 + latent["financial_headroom"] + latent["hidden_noise"]
    gp01_takeup = make_takeup(score_gp01, has_car, 0.06, rng)
    
    is_homeowner = customers["home_owner"]
    score_gp02 = latent["green_affinity"] * 1.5 + latent["financial_headroom"] * 2 + latent["hidden_noise"]
    gp02_takeup = make_takeup(score_gp02, is_homeowner, 0.045, rng)
    
    score_gp03 = latent["green_affinity"] * 3 + latent["financial_headroom"] + latent["hidden_noise"]
    gp03_takeup = make_takeup(score_gp03, is_homeowner, 0.035, rng)
    
    has_paper = customers["digital_usage"] < 0.5
    score_gp04 = latent["digital_propensity"] * 4 + latent["green_affinity"] + latent["hidden_noise"]
    gp04_takeup = make_takeup(score_gp04, has_paper, 0.20, rng)
    
    labels_df = pd.DataFrame({
        "customer_id": customers["customer_id"],
        "take_up_GP01": gp01_takeup,
        "take_up_GP02": gp02_takeup,
        "take_up_GP03": gp03_takeup,
        "take_up_GP04": gp04_takeup
    })
    
    tx_labels = tables["transactions"][["transaction_id", "true_category"]].copy()
    
    return {"take_up_labels": labels_df, "transaction_labels": tx_labels}
