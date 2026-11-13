from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .checkpoints import compute_merkle_root, generate_keypair, sign
from .models import Checkpoint, LedgerRecord

CHECKPOINT_INTERVAL = 10


def _canonical_json(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()


class LedgerStore:
    def __init__(self, db_path: Path | str = ":memory:") -> None:
        self._db_path = str(db_path)
        self._conn: sqlite3.Connection = sqlite3.connect(
            self._db_path, check_same_thread=False
        )
        self._init_schema()
        self._ensure_keypair()

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_hash TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                tool TEXT NOT NULL,
                decision TEXT NOT NULL,
                reason TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                arguments_hash TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merkle_root TEXT NOT NULL,
                record_ids TEXT NOT NULL,
                signature BLOB NOT NULL,
                public_key_pem BLOB NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS keypairs (
                id INTEGER PRIMARY KEY,
                private_pem BLOB NOT NULL,
                public_pem BLOB NOT NULL
            );
        """)
        self._conn.commit()

    def _ensure_keypair(self) -> None:
        row = self._conn.execute("SELECT id FROM keypairs LIMIT 1").fetchone()
        if not row:
            priv, pub = generate_keypair()
            self._conn.execute(
                "INSERT INTO keypairs (id, private_pem, public_pem) VALUES (1, ?, ?)",
                (priv, pub),
            )
            self._conn.commit()

    def _get_private_pem(self) -> bytes:
        row = self._conn.execute(
            "SELECT private_pem FROM keypairs WHERE id=1"
        ).fetchone()
        return bytes(row[0])

    def _get_public_pem(self) -> bytes:
        row = self._conn.execute(
            "SELECT public_pem FROM keypairs WHERE id=1"
        ).fetchone()
        return bytes(row[0])

    def _last_hash(self) -> str:
        row = self._conn.execute(
            "SELECT record_hash FROM records ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else "genesis"

    def _record_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM records").fetchone()
        return row[0]

    def append(
        self,
        agent_id: str,
        tool: str,
        decision: str,
        reason: str,
        rule_id: str,
        arguments: dict[str, Any],
    ) -> LedgerRecord:
        ts = datetime.now(UTC).isoformat()
        prev_hash = self._last_hash()
        arguments_hash = _sha256_hex(_canonical_json(arguments))

        record_dict = {
            "agent_id": agent_id,
            "arguments_hash": arguments_hash,
            "decision": decision,
            "prev_hash": prev_hash,
            "reason": reason,
            "rule_id": rule_id,
            "timestamp": ts,
            "tool": tool,
        }
        record_hash = _sha256_hex(_canonical_json(record_dict))

        cur = self._conn.execute(
            """INSERT INTO records
               (record_hash, prev_hash, agent_id, tool, decision, reason, rule_id, arguments_hash, timestamp)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                record_hash,
                prev_hash,
                agent_id,
                tool,
                decision,
                reason,
                rule_id,
                arguments_hash,
                ts,
            ),
        )
        self._conn.commit()
        record_id = cur.lastrowid or 0

        count = self._record_count()
        if count % CHECKPOINT_INTERVAL == 0:
            self._create_checkpoint(count)

        return LedgerRecord(
            id=record_id,
            record_hash=record_hash,
            prev_hash=prev_hash,
            agent_id=agent_id,
            tool=tool,
            decision=decision,
            reason=reason,
            rule_id=rule_id,
            arguments_hash=arguments_hash,
            timestamp=datetime.fromisoformat(ts),
        )

    def _create_checkpoint(self, up_to_count: int) -> None:
        start = max(1, up_to_count - CHECKPOINT_INTERVAL + 1)
        rows = self._conn.execute(
            "SELECT id, record_hash FROM records WHERE id >= ? AND id <= ?",
            (start, up_to_count),
        ).fetchall()
        record_ids = ",".join(str(r[0]) for r in rows)
        hashes = [r[1] for r in rows]
        merkle_root = compute_merkle_root(hashes)
        priv = self._get_private_pem()
        pub = self._get_public_pem()
        signature = sign(priv, merkle_root.encode())
        created_at = datetime.now(UTC).isoformat()
        self._conn.execute(
            "INSERT INTO checkpoints (merkle_root, record_ids, signature, public_key_pem, created_at) VALUES (?,?,?,?,?)",
            (merkle_root, record_ids, signature, pub, created_at),
        )
        self._conn.commit()

    def get_all(self) -> list[LedgerRecord]:
        rows = self._conn.execute(
            "SELECT id, record_hash, prev_hash, agent_id, tool, decision, reason, rule_id, arguments_hash, timestamp FROM records ORDER BY id"
        ).fetchall()
        return [
            LedgerRecord(
                id=r[0],
                record_hash=r[1],
                prev_hash=r[2],
                agent_id=r[3],
                tool=r[4],
                decision=r[5],
                reason=r[6],
                rule_id=r[7],
                arguments_hash=r[8],
                timestamp=datetime.fromisoformat(r[9]),
            )
            for r in rows
        ]

    def get_checkpoints(self) -> list[Checkpoint]:
        rows = self._conn.execute(
            "SELECT id, merkle_root, record_ids, signature, public_key_pem, created_at FROM checkpoints ORDER BY id"
        ).fetchall()
        return [
            Checkpoint(
                id=r[0],
                merkle_root=r[1],
                record_ids=r[2],
                signature=bytes(r[3]),
                public_key_pem=bytes(r[4]),
                created_at=datetime.fromisoformat(r[5]),
            )
            for r in rows
        ]

    def close(self) -> None:
        self._conn.close()
