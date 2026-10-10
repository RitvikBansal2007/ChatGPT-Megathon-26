import pandas as pd
from greendash.categoriser.rules import categorize_batch
from greendash.categoriser.model import predict_batch
import os

def save_examples():
    gold_path = os.path.join(os.path.dirname(__file__), '../../../gold_set.csv')
    df = pd.read_csv(gold_path)
    
    X = df['string'].values
    y = df['true_category'].values
    
    rules_preds = categorize_batch(X)
    ml_preds = predict_batch(X)
    
    combined_preds = []
    for r_pred, m_pred in zip(rules_preds, ml_preds):
        if r_pred != "Other":
            combined_preds.append(r_pred)
        else:
            combined_preds.append(m_pred)
            
    df['prediction'] = combined_preds
    df['is_correct'] = df['prediction'] == df['true_category']
    
    # 7 correct, 3 incorrect
    correct = df[df['is_correct']].sample(7, random_state=42)
    incorrect = df[~df['is_correct']].sample(min(3, len(df[~df['is_correct']])), random_state=42)
    
    worked = pd.concat([correct, incorrect])
    
    out_path = os.path.join(os.path.dirname(__file__), 'worked_examples.csv')
    worked.to_csv(out_path, index=False)
    print(f"Saved {len(worked)} worked examples to {out_path}")

if __name__ == "__main__":
    save_examples()
