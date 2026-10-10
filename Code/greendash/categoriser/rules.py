import yaml
import os

def load_rules():
    config_path = os.path.join(os.path.dirname(__file__), '../../config/categories.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['rules']

def categorize_transaction(txn_string, rules=None):
    """
    Returns the first rule category where any keyword is a substring 
    of the transaction string (case insensitive). Defaults to 'Other'.
    """
    if rules is None:
        rules = load_rules()
    
    if not txn_string or not isinstance(txn_string, str):
        return "Other"
        
    txn_lower = txn_string.lower()
    for rule in rules:
        category = rule['category']
        keywords = rule['keywords']
        for kw in keywords:
            if kw.lower() in txn_lower:
                return category
    
    return "Other"

def categorize_batch(txn_strings):
    rules = load_rules()
    return [categorize_transaction(txn, rules) for txn in txn_strings]
