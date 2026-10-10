-- GreenProof SQLite Core Schema
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    role TEXT NOT NULL DEFAULT 'customer',
    account_status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    amount TEXT NOT NULL,              -- Validated decimal string (no float conversion)
    currency TEXT DEFAULT NULL,        -- NULL when source has no currency (no implicit GBP)
    debit_credit TEXT DEFAULT NULL,    -- 'debit', 'credit', or NULL if unspecified
    category TEXT DEFAULT NULL,        -- Must be one of the 8 canonical categories or NULL
    import_batch_id TEXT DEFAULT NULL, -- UUID or tag for CSV batch tracking
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_transactions_batch ON transactions(import_batch_id);
