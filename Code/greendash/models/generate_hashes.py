import hashlib
import json
import os
import glob

def generate_hashes():
    models_dir = os.path.join(os.path.dirname(__file__), '../../data/models')
    hashes = {}
    
    for model_path in glob.glob(os.path.join(models_dir, '*.skops')):
        with open(model_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
            filename = os.path.basename(model_path)
            hashes[filename] = file_hash
            
    hash_file = os.path.join(models_dir, 'hashes.json')
    with open(hash_file, 'w') as f:
        json.dump(hashes, f, indent=2)
    print("Hashes saved to", hash_file)

if __name__ == "__main__":
    generate_hashes()
