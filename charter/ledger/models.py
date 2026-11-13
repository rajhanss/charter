from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class LedgerRecord:
    id: int
    record_hash: str
    prev_hash: str
    agent_id: str
    tool: str
    decision: str
    reason: str
    rule_id: str
    arguments_hash: str
    timestamp: datetime


@dataclass
class Checkpoint:
    id: int
    merkle_root: str
    record_ids: str
    signature: bytes
    public_key_pem: bytes
    created_at: datetime
