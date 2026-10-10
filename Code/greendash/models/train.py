from greendash.models.utils import load_data, get_features_and_targets
import lightgbm as lgb
import skops.io as sio
import pandas as pd
import numpy as np
import os

def train_lgb():
    train_df, val_df, _ = load_data()
    X_train, Y_train = get_features_and_targets(train_df)
    X_val, Y_val = get_features_and_targets(val_df)
    
    out_dir = os.path.join(os.path.dirname(__file__), '../../data/models')
    os.makedirs(out_dir, exist_ok=True)
    
    models = {}
    
    for target in Y_train.columns:
        print(f"\nTraining LightGBM for {target}...")
        
        # Define monotone constraints (+1 for positive correlation, -1 for negative, 0 for none)
        # Using 1 for features we know should positively impact take_up to satisfy PRD
        monotone_constraints = []
        for col in X_train.columns:
            if 'fuel' in col and target == 'take_up_GP01':
                monotone_constraints.append(1)
            elif 'gas' in col and target == 'take_up_GP02':
                monotone_constraints.append(1)
            elif 'electricity' in col and target == 'take_up_GP03':
                monotone_constraints.append(1)
            elif 'paper' in col and target == 'take_up_GP04':
                monotone_constraints.append(1)
            else:
                monotone_constraints.append(0)
                
        clf = lgb.LGBMClassifier(
            n_estimators=100,
            monotone_constraints=monotone_constraints,
            random_state=42,
            importance_type='gain'
        )
        
        clf.fit(
            X_train, Y_train[target],
            eval_set=[(X_val, Y_val[target])],
            callbacks=[lgb.early_stopping(stopping_rounds=10)]
        )
        
        model_path = os.path.join(out_dir, f'{target}_lgb.skops')
        sio.dump(clf, model_path)
        models[target] = clf
        print(f"Saved model to {model_path}")

if __name__ == "__main__":
    train_lgb()
