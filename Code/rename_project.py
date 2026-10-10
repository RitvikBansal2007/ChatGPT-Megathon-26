import os
import subprocess
from pathlib import Path

def replace_in_file(file_path):
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception:
        return
    
    new_content = content.replace("GreenDash", "GreenDash")
    new_content = new_content.replace("greendash", "greendash")
    
    if new_content != content:
        file_path.write_text(new_content, encoding='utf-8')
        print(f"Updated {file_path}")

def main():
    root = "/Users/aniketgoel/Desktop/hackathon/Code"
    exts = {".py", ".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".sql", ".csv", ".html", ".js", ".css"}
    
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ('node_modules', 'out')]
        
        for f in filenames:
            if not f.startswith('.'):
                p = Path(dirpath) / f
                if p.suffix in exts or p.name == "Makefile":
                    replace_in_file(p)

    # Rename the directory using git mv so git tracks it
    old_dir = Path(root) / "greendash"
    new_dir = Path(root) / "greendash"
    if old_dir.exists() and old_dir.is_dir():
        subprocess.run(["git", "mv", "greendash", "greendash"], cwd=root)
        print("Git renamed greendash to greendash")

if __name__ == "__main__":
    main()
