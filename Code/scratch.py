import pandas as pd
df = pd.read_parquet("data/features/features.parquet")
print(df[df['customer_id'] == 'CUST-0001'].T)
