import sqlite3, pytest
from greendash.db import audit, migrate
from config.settings import settings

def test_chain_ok_then_tamper_detected(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DB_PATH", str(tmp_path / "t.db"))
    migrate.migrate()
    audit.append("k1", "GP01", "PASS", [], "llm")
    audit.append("k1", "GP01", "BLOCKED", ["NUM", "BAN"], "red_team")
    assert audit.verify_chain() == (True, None)

    raw = sqlite3.connect(settings.DB_PATH)
    with pytest.raises(sqlite3.DatabaseError):
        raw.execute("UPDATE claim_audit SET verdict='PASS' WHERE id=2")
    raw.execute("DROP TRIGGER claim_audit_no_update")
    raw.execute("UPDATE claim_audit SET verdict='PASS' WHERE id=2")
    raw.commit()
    ok, bad_id = audit.verify_chain()
    assert ok is False and bad_id == 2
