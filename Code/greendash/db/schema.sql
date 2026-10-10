PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  user_key   TEXT PRIMARY KEY,
  role       TEXT NOT NULL CHECK (role IN
             ('CUSTOMER','RELATIONSHIP_MANAGER','PORTFOLIO_ANALYST','AUDITOR','EVALUATOR','SERVICE')),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claim_audit (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  ts             TEXT NOT NULL,
  customer_key   TEXT NOT NULL,
  product_id     TEXT NOT NULL,
  verdict        TEXT NOT NULL CHECK (verdict IN ('PASS','BLOCKED','FALLBACK','PII_BLOCK')),
  rules_violated TEXT NOT NULL,
  source         TEXT NOT NULL CHECK (source IN ('llm','template','red_team')),
  prev_hash      TEXT NOT NULL,
  row_hash       TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS claim_audit_no_update
BEFORE UPDATE ON claim_audit
BEGIN SELECT RAISE(ABORT, 'claim_audit is append-only'); END;

CREATE TRIGGER IF NOT EXISTS claim_audit_no_delete
BEFORE DELETE ON claim_audit
BEGIN SELECT RAISE(ABORT, 'claim_audit is append-only'); END;

CREATE TABLE IF NOT EXISTS scenario_runs (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  ts            TEXT NOT NULL,
  customer_key  TEXT NOT NULL,
  mutations     TEXT NOT NULL,
  before_status TEXT NOT NULL,
  after_status  TEXT NOT NULL,
  elapsed_ms    INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  ts           TEXT NOT NULL,
  customer_key TEXT NOT NULL,
  product_id   TEXT NOT NULL,
  kind         TEXT NOT NULL CHECK (kind IN ('NOT_RELEVANT','THIS_IS_WRONG','REMIND_LATER')),
  note_enc     BLOB
);

CREATE TABLE IF NOT EXISTS optouts (
  customer_key TEXT PRIMARY KEY,
  opted_out    INTEGER NOT NULL CHECK (opted_out IN (0,1)),
  updated_at   TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_customer ON claim_audit(customer_key);
CREATE INDEX IF NOT EXISTS idx_feedback_customer ON feedback(customer_key);
