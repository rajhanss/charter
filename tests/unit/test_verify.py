import sqlite3

from charter.ledger.store import LedgerStore
from charter.ledger.verify import verify_chain


def test_clean_chain_verifies(tmp_path):
    db_file = tmp_path / "clean.db"
    store = LedgerStore(db_file)
    store.append("a1", "t1", "allow", "ok", "r1", {"a": 1})
    store.append("a1", "t2", "deny", "blocked", "r2", {"b": 2})
    store.append("a1", "t3", "require_approval", "manual", "r3", {"c": 3})

    result = verify_chain(store)
    store.close()
    assert result.valid is True
    assert len(result.errors) == 0


def test_mutate_field_detected(tmp_path):
    db_file = tmp_path / "tamper_field.db"
    store = LedgerStore(db_file)
    store.append("a1", "t1", "allow", "ok", "r1", {})
    store.append("a1", "t2", "deny", "blocked", "r2", {})
    store.close()

    # Tamper with record 2 in the database directly
    conn = sqlite3.connect(str(db_file))
    conn.execute("UPDATE records SET decision='allow' WHERE id=2")
    conn.commit()
    conn.close()

    reopened = LedgerStore(db_file)
    result = verify_chain(reopened)
    reopened.close()

    assert result.valid is False
    assert any("hash mismatch" in err for err in result.errors)


def test_delete_record_detected(tmp_path):
    db_file = tmp_path / "tamper_del.db"
    store = LedgerStore(db_file)
    store.append("a1", "t1", "allow", "ok", "r1", {})
    store.append("a1", "t2", "allow", "ok", "r1", {})
    store.append("a1", "t3", "allow", "ok", "r1", {})
    store.close()

    # Delete record 2 from SQLite
    conn = sqlite3.connect(str(db_file))
    conn.execute("DELETE FROM records WHERE id=2")
    conn.commit()
    conn.close()

    reopened = LedgerStore(db_file)
    result = verify_chain(reopened)
    reopened.close()

    assert result.valid is False
    assert any("prev_hash mismatch" in err for err in result.errors)


def test_insert_record_detected(tmp_path):
    db_file = tmp_path / "tamper_ins.db"
    store = LedgerStore(db_file)
    store.append("a1", "t1", "allow", "ok", "r1", {})
    store.append("a1", "t2", "allow", "ok", "r1", {})
    store.close()

    # Insert an unchained record
    conn = sqlite3.connect(str(db_file))
    conn.execute(
        """INSERT INTO records (id, record_hash, prev_hash, agent_id, tool, decision, reason, rule_id, arguments_hash, timestamp)
           VALUES (99, 'fakehash', 'fakeprev', 'hacker', 'exploit', 'allow', 'forged', 'r0', 'fake', '2026-11-13T00:00:00Z')"""
    )
    conn.commit()
    conn.close()

    reopened = LedgerStore(db_file)
    result = verify_chain(reopened)
    reopened.close()

    assert result.valid is False


def test_corrupt_checkpoint_signature_detected(tmp_path):
    db_file = tmp_path / "tamper_cp.db"
    store = LedgerStore(db_file)
    for i in range(10):
        store.append("a1", f"tool_{i}", "allow", "ok", "r1", {})
    store.close()

    # Corrupt the signature of checkpoint 1
    conn = sqlite3.connect(str(db_file))
    conn.execute("UPDATE checkpoints SET signature=X'deadbeef' WHERE id=1")
    conn.commit()
    conn.close()

    reopened = LedgerStore(db_file)
    result = verify_chain(reopened)
    reopened.close()

    assert result.valid is False
    assert any("signature invalid" in err for err in result.errors)
