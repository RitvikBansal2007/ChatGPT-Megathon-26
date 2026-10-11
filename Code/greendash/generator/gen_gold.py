import pandas as pd
import numpy as np
from merchants import noisy_string, TEMPLATES

rng = np.random.default_rng(42)
templates = rng.choice(TEMPLATES, size=200)

merchants = [noisy_string(t, rng) for t in templates]
categories = [t.true_category for t in templates]

df = pd.DataFrame({
    "string": merchants,
    "true_category": categories
})

df.to_csv("../../../gold_set.csv", index=False)
