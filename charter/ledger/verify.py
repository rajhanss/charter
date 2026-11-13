from __future__ import annotations

from dataclasses import dataclass

from .checkpoints import compute_merkle_root, verify_signature
from .store import LedgerStore, _canonical_json, _sha256_hex


@dataclass
class VerifyResult:
    valid: bool
    errors: list[str]


def verify_chain(store: LedgerStore) -> VerifyResult:
    """
    Verify the integrity of the ledger.

    Limitation: tail truncation (deletion of the last N records after the
    latest checkpoint) cannot be detected by hash-chain verification alone.
    To detect truncation, anchor the latest checkpoint's merkle_root in an
    external system (e.g., a git tag or a transparency log) and compare on
    verify.
    """
    errors: list[str] = []
    records = store.get_all()

    prev = "genesis"
    for rec in records:
        # Recompute the hash
        record_dict = {
            "agent_id": rec.agent_id,
            "arguments_hash": rec.arguments_hash,
            "decision": rec.decision,
            "prev_hash": rec.prev_hash,
            "reason": rec.reason,
            "rule_id": rec.rule_id,
            "timestamp": rec.timestamp.isoformat(),
            "tool": rec.tool,
        }
        expected_hash = _sha256_hex(_canonical_json(record_dict))
        if rec.record_hash != expected_hash:
            errors.append(
                f"Record {rec.id}: hash mismatch (stored={rec.record_hash[:16]}... expected={expected_hash[:16]}...)"
            )
        if rec.prev_hash != prev:
            errors.append(f"Record {rec.id}: prev_hash mismatch")
        prev = rec.record_hash

    # Verify checkpoints
    checkpoints = store.get_checkpoints()
    for cp in checkpoints:
        ids = [int(x) for x in cp.record_ids.split(",")]
        cp_records = [r for r in records if r.id in ids]
        merkle_root = compute_merkle_root([r.record_hash for r in cp_records])
        if merkle_root != cp.merkle_root:
            errors.append(f"Checkpoint {cp.id}: merkle root mismatch")
        if not verify_signature(
            cp.public_key_pem, cp.signature, cp.merkle_root.encode()
        ):
            errors.append(f"Checkpoint {cp.id}: signature invalid")

    return VerifyResult(valid=len(errors) == 0, errors=errors)
