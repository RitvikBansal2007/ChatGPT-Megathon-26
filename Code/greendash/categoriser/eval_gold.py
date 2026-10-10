import pandas as pd
from sklearn.metrics import f1_score
from greendash.categoriser.rules import categorize_batch
from greendash.categoriser.model import predict_batch
import os

def evaluate_gold():
    # Read gold set
    gold_path = os.path.join(os.path.dirname(__file__), '../../../gold_set.csv')
    df = pd.read_csv(gold_path)
    
    X = df['string'].values
    y = df['true_category'].values
    
    # Predict using rules
    rules_preds = categorize_batch(X)
    
    # Predict using ML
    ml_preds = predict_batch(X)
    
    # Combined logic
    combined_preds = []
    for r_pred, m_pred in zip(rules_preds, ml_preds):
        if r_pred != "Other":
            combined_preds.append(r_pred)
        else:
            combined_preds.append(m_pred)
            
    macro_f1 = f1_score(y, combined_preds, average='macro')
    accuracy = (np.array(combined_preds) == y).mean()
    
    print(f"Gold Set Combined Macro-F1: {macro_f1:.4f}")
    print(f"Gold Set Combined Accuracy: {accuracy:.4f}")

if __name__ == "__main__":
    import numpy as np
    evaluate_gold()
