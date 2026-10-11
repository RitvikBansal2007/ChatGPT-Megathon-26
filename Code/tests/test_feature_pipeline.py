import os
import pandas as pd
import pytest
import json
from tempfile import TemporaryDirectory
from scripts.make_real_features import build_features
from greendash.models.split import create_splits

def test_temporal_leakage():
    with TemporaryDirectory() as tmp_dir:
        raw_dir = os.path.join(tmp_dir, 'raw')
        out_dir = os.path.join(tmp_dir, 'features')
        os.makedirs(raw_dir)
        
        # 1. Create dummy data
        customers = pd.DataFrame({
            'customer_id': ['CUST-001', 'CUST-002']
        })
        customers.to_csv(f'{raw_dir}/customers.csv', index=False)
        
        labels = pd.DataFrame({
            'customer_id': ['CUST-001', 'CUST-002'],
            'take_up_GP01': [0, 1]
        })
        labels.to_csv(f'{raw_dir}/take_up_labels.csv', index=False)
        
        txns = pd.DataFrame({
            'transaction_id': [1, 2, 3],
            'customer_id': ['CUST-001', 'CUST-001', 'CUST-002'],
            'date': ['2011-05-01', '2011-06-15', '2011-05-15'], # Cutoff is 2011-06-01
            'merchant_description': ['A', 'B', 'C'],
            'amount': [100.0, 500.0, 200.0],
            'debit_credit': ['debit', 'debit', 'debit'],
            'true_category': ['Fuel', 'Fuel', 'Fuel']
        })
        txns.to_csv(f'{raw_dir}/transactions.csv', index=False)
        
        # Create empty vehicles, digital, energy to avoid errors in merge
        vehicles = pd.DataFrame(columns=['customer_id', 'annual_mileage'])
        vehicles.to_csv(f'{raw_dir}/vehicles.csv', index=False)
        
        digital = pd.DataFrame(columns=['customer_id', 'month', 'paper_statements', 'digital_transactions'])
        digital.to_csv(f'{raw_dir}/digital_usage.csv', index=False)
        
        energy = pd.DataFrame(columns=['customer_id', 'month', 'electricity_kwh', 'gas_kwh'])
        energy.to_csv(f'{raw_dir}/energy_usage.csv', index=False)
        
        # 2. Run feature builder
        build_features(cutoff_date='2011-06-01', raw_dir=raw_dir, out_dir=out_dir)
        
        # 3. Assertions
        features = pd.read_parquet(f'{out_dir}/features.parquet')
        
        c1_features = features[features['customer_id'] == 'CUST-001'].iloc[0]
        c2_features = features[features['customer_id'] == 'CUST-002'].iloc[0]
        
        # CUST-001 has 100 before cutoff and 500 after cutoff. The 500 should be excluded.
        assert c1_features['fuel_spend_last_6m'] == 100.0, "Temporal leakage detected in fuel_spend_last_6m"
        
        # CUST-002 has 200 before cutoff
        assert c2_features['fuel_spend_last_6m'] == 200.0

def test_split_integrity(monkeypatch):
    with TemporaryDirectory() as tmp_dir:
        features_dir = os.path.join(tmp_dir, 'features')
        splits_dir = os.path.join(tmp_dir, 'splits')
        os.makedirs(features_dir)
        os.makedirs(splits_dir)
        
        # Dummy features
        df = pd.DataFrame({
            'customer_id': [f'CUST-{i}' for i in range(100)],
            'take_up_GP01': [i % 2 for i in range(100)],
            'is_persona': [i < 10 for i in range(100)], # First 10 are personas
            'age': [30] * 100 # Should trigger leakage error
        })
        df.to_parquet(f'{features_dir}/features.parquet')
        
        # Paths are passed in: patching json.dump used to leave the real splits.json truncated to 0 bytes
        paths = dict(features_path=f'{features_dir}/features.parquet', out_dir=splits_dir)

        # Age should trigger error
        with pytest.raises(ValueError, match="Leakage/bias detected"):
            create_splits(**paths)
            
        # Fix dataframe
        df.drop(columns=['age'], inplace=True)
        df.to_parquet(f'{features_dir}/features.parquet')
        
        # Create splits
        create_splits(**paths)
        
        with open(f'{splits_dir}/splits.json', 'r') as f:
            splits = json.load(f)
            
        train_s = set(splits['train'])
        val_s = set(splits['val'])
        test_s = set(splits['test'])
        
        assert len(train_s.intersection(val_s)) == 0
        assert len(train_s.intersection(test_s)) == 0
        assert len(val_s.intersection(test_s)) == 0
        
        # Check personas are excluded from train/val/test
        personas = set(splits['personas'])
        assert len(personas) == 10
        assert len(train_s.intersection(personas)) == 0
