import pandas as pd
import numpy as np
import os

def create_fake_data(num_rows=5000):
    np.random.seed(42)
    
    # Generate fake features
    data = {
        "customer_id": [f"CUST-{i:05d}" for i in range(1, num_rows + 1)],
        "fuel_spend_last_6m": np.random.exponential(scale=100, size=num_rows),
        "annual_mileage": np.random.normal(loc=8000, scale=3000, size=num_rows).clip(min=0),
        "electricity_kwh_last_year": np.random.normal(loc=2900, scale=500, size=num_rows).clip(min=0),
        "gas_kwh_last_year": np.random.normal(loc=12000, scale=3000, size=num_rows).clip(min=0),
        "paper_statements": np.random.choice([0, 1], size=num_rows, p=[0.7, 0.3]),
        "digital_transactions": np.random.poisson(lam=20, size=num_rows),
        
        # 4 fake labels (target variable = take_up 0 or 1)
        # GP01 EV Finance (4-8% base rate)
        "take_up_GP01": np.random.choice([0, 1], size=num_rows, p=[0.94, 0.06]),
        # GP02 Green Home Loan (3-6% base rate)
        "take_up_GP02": np.random.choice([0, 1], size=num_rows, p=[0.95, 0.05]),
        # GP03 Solar Finance (2-5% base rate)
        "take_up_GP03": np.random.choice([0, 1], size=num_rows, p=[0.96, 0.04]),
        # GP04 Paperless Banking (15-25% base rate)
        "take_up_GP04": np.random.choice([0, 1], size=num_rows, p=[0.80, 0.20])
    }
    
    df = pd.DataFrame(data)
    
    # Add strong signal for positive labels so the models can actually learn something
    # GP01: Higher fuel spend -> higher chance
    df.loc[df['take_up_GP01'] == 1, 'fuel_spend_last_6m'] += np.random.normal(200, 50, sum(df['take_up_GP01']))
    # GP02: Higher gas usage -> higher chance
    df.loc[df['take_up_GP02'] == 1, 'gas_kwh_last_year'] += np.random.normal(3000, 1000, sum(df['take_up_GP02']))
    # GP04: paper statements -> higher chance of paperless switch
    df.loc[df['take_up_GP04'] == 1, 'paper_statements'] = 1
    
    # Save the file
    os.makedirs('data/features', exist_ok=True)
    df.to_parquet('data/features/features.parquet')
    print(f"Generated fake features for {num_rows} customers at data/features/features.parquet")

if __name__ == "__main__":
    create_fake_data()
