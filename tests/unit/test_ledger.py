def test_append_increments_id(mem_store):
    r1 = mem_store.append("a1", "t1", "allow", "ok", "r1", {"k": 1})
    r2 = mem_store.append("a1", "t2", "deny", "blocked", "r2", {"k": 2})
    assert r1.id == 1
    assert r2.id == 2


def test_hash_chain_correct(mem_store):
    r1 = mem_store.append("a1", "t1", "allow", "ok", "r1", {})
    r2 = mem_store.append("a1", "t2", "allow", "ok", "r1", {})
    r3 = mem_store.append("a1", "t3", "allow", "ok", "r1", {})

    assert r1.prev_hash == "genesis"
    assert r2.prev_hash == r1.record_hash
    assert r3.prev_hash == r2.record_hash


def test_genesis_prev_hash(mem_store):
    r = mem_store.append("agent-alpha", "init", "allow", "init", "rule-0", {})
    assert r.prev_hash == "genesis"


def test_arguments_stored_as_hash(mem_store):
    args = {"secret_token": "super-secret-value-12345", "user_id": 42}
    r = mem_store.append("a1", "api_call", "allow", "ok", "r1", args)
    # Must be 64-character SHA-256 hex string
    assert len(r.arguments_hash) == 64
    assert isinstance(r.arguments_hash, str)
    # The plaintext secret must not appear in the hash string
    assert "super-secret-value" not in r.arguments_hash


def test_checkpoint_created_every_10(mem_store):
    assert len(mem_store.get_checkpoints()) == 0

    for i in range(10):
        mem_store.append("a1", f"tool_{i}", "allow", "ok", "r1", {"i": i})

    cps = mem_store.get_checkpoints()
    assert len(cps) == 1
    cp = cps[0]
    assert cp.id == 1
    assert len(cp.signature) > 0
    assert len(cp.merkle_root) == 64
    assert "1,2,3,4,5,6,7,8,9,10" in cp.record_ids
