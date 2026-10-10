import numpy as np

def make_latent(n: int, rng: np.random.Generator) -> dict:
    """
    Generate hidden drivers that are never given to the model.
    These influence observed behaviour and product take-up.
    """
    return {
        "green_affinity": rng.beta(2, 5, n),
        "financial_headroom": rng.standard_normal(n),
        "digital_propensity": rng.beta(3, 2, n),
        "car_finance_ending": rng.random(n) < 0.12,
        "mortgage_started": rng.random(n) < 0.05,
        "recently_moved": rng.random(n) < 0.06,
        "car_sold": rng.random(n) < 0.03,
        "hidden_noise": rng.standard_normal(n),
    }
