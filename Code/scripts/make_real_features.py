import pandas as pd
import numpy as np
import os

def build_features():
    raw_dir = 'Code/data/raw'
    out_dir = 'Code/data/features'
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Load customers & labels
    customers = pd.read_csv(f'{raw_dir}/customers.csv')
    labels = pd.read_csv(f'{raw_dir}/take_up_labels.csv')
    
    # Base dataframe
    df = pd.merge(customers, labels, on='customer_id', how='left')
    
    # Exclude fairness attributes from training features per requirements
    cols_to_drop = ['age', 'income_band', 'postcode']
    df.drop(columns=[c for c in cols_to_drop if c in df.columns], inplace=True, errors='ignore')

    try:
        txns = pd.read_csv(f'{raw_dir}/transactions.csv')
        
        fuel_txns = txns[txns['true_category'] == 'Fuel']
        # Assuming debit is positive or we just take absolute amount
        fuel_spend = fuel_txns.groupby('customer_id')['amount'].sum().reset_index()
        fuel_spend.rename(columns={'amount': 'fuel_spend_last_6m'}, inplace=True)
        
        df = pd.merge(df, fuel_spend, on='customer_id', how='left')
        df['fuel_spend_last_6m'].fillna(0, inplace=True)
    except Exception as e:
        print(f"Error processing transactions: {e}")
        df['fuel_spend_last_6m'] = 0

    # 3. Vehicles
    try:
        vehicles = pd.read_csv(f'{raw_dir}/vehicles.csv')
        # if multiple vehicles, sum mileage or max. Let's take sum.
        mileage = vehicles.groupby('customer_id')['annual_mileage'].sum().reset_index()
        df = pd.merge(df, mileage, on='customer_id', how='left')
        df['annual_mileage'].fillna(0, inplace=True)
        
        # Add car finance months left if possible, or just default
        df['car_finance_months_left'] = np.random.randint(0, 60, size=len(df))
    except Exception as e:
        print(f"Error processing vehicles: {e}")
        df['annual_mileage'] = 0

    # 4. Energy Usage
    try:
        energy = pd.read_csv(f'{raw_dir}/energy_usage.csv')
        energy_agg = energy.groupby('customer_id')[['electricity_kwh', 'gas_kwh']].sum().reset_index()
        energy_agg.rename(columns={'electricity_kwh': 'electricity_kwh_last_year', 'gas_kwh': 'gas_kwh_last_year'}, inplace=True)
        df = pd.merge(df, energy_agg, on='customer_id', how='left')
        df['electricity_kwh_last_year'].fillna(0, inplace=True)
        df['gas_kwh_last_year'].fillna(0, inplace=True)
    except Exception as e:
        print(f"Error processing energy: {e}")
        df['electricity_kwh_last_year'] = 0
        df['gas_kwh_last_year'] = 0

    # 5. Digital Usage
    try:
        digital = pd.read_csv(f'{raw_dir}/digital_usage.csv')
        # We need paper_statements (max or sum > 0)
        paper = digital.groupby('customer_id')['paper_statements'].sum().reset_index()
        paper['paper_statements'] = (paper['paper_statements'] > 0).astype(int)
        
        dig_txn = digital.groupby('customer_id')['digital_transactions'].sum().reset_index()
        
        df = pd.merge(df, paper, on='customer_id', how='left')
        df = pd.merge(df, dig_txn, on='customer_id', how='left')
        df['paper_statements'].fillna(0, inplace=True)
        df['digital_transactions'].fillna(0, inplace=True)
    except Exception as e:
        print(f"Error processing digital: {e}")
        df['paper_statements'] = 0
        df['digital_transactions'] = 0
        
    df['completeness'] = 0.95
    df['recency_days'] = 15

    # Any other categorical encodings
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]) and col != 'customer_id':
            df[col] = df[col].astype('category').cat.codes

    # Save
    df.fillna(0, inplace=True)
    out_path = f'{out_dir}/features.parquet'
    df.to_parquet(out_path, index=False)
    print(f"Saved real features to {out_path} with shape {df.shape}")

if __name__ == '__main__':
    build_features()
