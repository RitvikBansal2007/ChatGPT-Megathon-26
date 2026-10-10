import pandas as pd
import numpy as np

def build_final_features():
    print("Loading lcl_aggregated...")
    # 1. Load the aggregated LCL data
    lcl_df = pd.read_csv('Code/data/raw/lcl_aggregated.csv', header=None, names=['LCLid', 'total_kwh'])
    # Sort to make deterministic
    lcl_df.sort_values('LCLid', inplace=True)
    
    print("Loading features.parquet...")
    # 2. Load existing features
    features_df = pd.read_parquet('Code/data/features/features.parquet')
    features_df.sort_values('customer_id', inplace=True)
    
    num_customers = len(features_df)
    
    # 3. Update electricity_kwh_last_year
    if len(lcl_df) < num_customers:
        print(f"Warning: Only {len(lcl_df)} households, we need {num_customers}.")
        kwh_values = lcl_df['total_kwh'].values
        kwh_values = np.pad(kwh_values, (0, max(0, num_customers - len(kwh_values))), mode='edge')
        kwh_values = kwh_values[:num_customers]
    else:
        kwh_values = lcl_df['total_kwh'].values[:num_customers]
        
    features_df['electricity_kwh_last_year'] = kwh_values
    
    print("Saving updated features...")
    features_df.to_parquet('Code/data/features/features.parquet', index=False)
    print("Done!")

if __name__ == "__main__":
    build_final_features()
