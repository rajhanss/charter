import random
import sqlite3

import pytest

from charter.ledger.store import LedgerStore
from charter.ledger.verify import verify_chain

rng = random.Random(1337)


@pytest.mark.parametrize("iteration", range(20))
def test_fuzz_ledger_tampering_always_detected(tmp_path, iteration):
    db_file = tmp_path / f"fuzz_ledger_{iteration}.db"
    store = LedgerStore(db_file)

    num_records = rng.randint(3, 25)
    for i in range(num_records):
        decision = rng.choice(["allow", "deny", "require_approval"])
        store.append(
            agent_id=f"agent-{rng.randint(1, 3)}",
            tool=f"tool_{rng.randint(1, 5)}",
            decision=decision,
            reason=f"Reason {i}",
            rule_id=f"rule-{rng.randint(1, 5)}",
            arguments={"idx": i, "val": rng.random()},
        )
    store.close()

    # Pre-tampering verification must pass
    clean_store = LedgerStore(db_file)
    clean_result = verify_chain(clean_store)
    clean_store.close()
    assert clean_result.valid is True

    # Tamper with the database
    conn = sqlite3.connect(str(db_file))
    tamper_mode = rng.choice(["mutate_field", "delete_record", "insert_record"])

    if tamper_mode == "mutate_field":
        target_id = rng.randint(1, num_records)
        conn.execute(
            "UPDATE records SET reason='tampered reason' WHERE id=?",
            (target_id,),
        )
    elif tamper_mode == "delete_record":
        # Deleting an intermediate record (1 to num_records - 1) breaks the chain for subsequent records
        target_id = rng.randint(1, max(1, num_records - 1))
        conn.execute("DELETE FROM records WHERE id=?", (target_id,))
    else:  # insert_record
        conn.execute(
            """INSERT INTO records (id, record_hash, prev_hash, agent_id, tool, decision, reason, rule_id, arguments_hash, timestamp)
               VALUES (9999, 'badhash', 'badprev', 'evil', 'exploit', 'allow', 'forged', 'r0', 'fake', '2026-11-13T00:00:00Z')"""
        )
    conn.commit()
    conn.close()

    # Verification must detect the tampering
    tampered_store = LedgerStore(db_file)
    tampered_result = verify_chain(tampered_store)
    tampered_store.close()

    assert tampered_result.valid is False
    assert len(tampered_result.errors) > 0
