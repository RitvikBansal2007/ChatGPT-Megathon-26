import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import pickle
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'categoriser_model.pkl')

def build_pipeline():
    return Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4), min_df=2)),
        ('clf', LogisticRegression(max_iter=1000, class_weight='balanced'))
    ])

def train_model(df):
    """
    Trains the model on dataframe containing 'merchant_description' and 'true_category'.
    """
    X = df['merchant_description']
    y = df['true_category']
    
    pipeline = build_pipeline()
    pipeline.fit(X, y)
    
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(pipeline, f)
        
    return pipeline

def load_model():
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'rb') as f:
            return pickle.load(f)
    return None

def predict_batch(txn_strings):
    model = load_model()
    if not model:
        raise Exception("Model not trained yet.")
    return model.predict(txn_strings)

if __name__ == "__main__":
    # If run directly, train on the raw dataset
    data_path = os.path.join(os.path.dirname(__file__), '../../data/raw/transactions.parquet')
    if os.path.exists(data_path):
        df = pd.read_parquet(data_path)
        print("Training categoriser model...")
        train_model(df)
        print("Model trained and saved to", MODEL_PATH)
    else:
        print("Training data not found at", data_path)
