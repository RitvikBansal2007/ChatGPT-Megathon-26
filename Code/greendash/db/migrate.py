import os
import sqlite3
from pathlib import Path

from config.settings import settings

SCHEMA = Path(__file__).with_name("schema.sql")

def migrate() -> None:
    db = Path(settings.DB_PATH)
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(SCHEMA.read_text())
        # Add columns if users table was created previously without them
        cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
        for col in ["email", "display_name", "password_hash"]:
            if col not in cols:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        conn.commit()
    finally:
        conn.close()
    os.chmod(db, 0o600)

if __name__ == "__main__":
    migrate()
    print("db ready:", settings.DB_PATH)
