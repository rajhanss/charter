# Charter Architecture

## Overview

Charter separates governance into a pure evaluation core and I/O at the edges.

```
+-------------------------------------------------------------+
|                      Autonomous Agent                       |
+-------------------------------------------------------------+
                              |
                     PolicyRequest (tool, args, autonomy)
                              v
+-------------------------------------------------------------+
|                    charter.policy.evaluator                 |
|            (Pure function: request + config -> result)      |
+-------------------------------------------------------------+
                              |
                     PolicyResult (decision, rule_id, reason)
                              v
+-------------------------------------------------------------+
|                    charter.ledger.store                     |
|         (SQLite append-only, SHA-256 hash chain)            |
+-------------------------------------------------------------+
                              |
                    Checkpoints every N records
                              v
+-------------------------------------------------------------+
|                  charter.ledger.checkpoints                 |
|             (Merkle root + Ed25519 signature)               |
+-------------------------------------------------------------+
                              |
                    Offline verification / Evidence
                              v
+-------------------------------------------------------------+
|             charter.evidence & charter.report               |
|      (Obligation mapping -> MD / HTML / JSON reports)       |
+-------------------------------------------------------------+
```

## Package Structure

```
charter/
  policy/      Deterministic policy evaluation (schema, evaluator)
  approvals/   Human approval lifecycle and timeout handling
  ledger/      Append-only decision log, hash chain, signed checkpoints, verify
  evidence/    Obligation catalog (EU AI Act, NIST, ISO) and coverage engine
  report/      Markdown, HTML, and JSON report generators
  adapters/    Python decorator, FastAPI middleware, agent protocols
  cli/         Typer CLI (check, replay, verify, report)
  service/     FastAPI HTTP wrapper
```

## Policy Evaluation Semantics

1. **Default Deny:** If no rules match the request, the evaluator returns `deny` with `rule_id="default-deny"`.
2. **Deny Precedence:** If multiple rules match, any matching `deny` rule takes precedence over `require_approval` and `allow`.
3. **Approval Precedence:** If no `deny` matches, any matching `require_approval` rule takes precedence over `allow`.
4. **Attribution:** Every decision strictly identifies the rule ID that fired.
5. **No Model Dependencies:** Policy evaluation is deterministic, pure Python without LLM involvement.

## Cryptographic Ledger

- **Canonical JSON:** Record content is serialized using sorted keys and compact separators (`",", ":"`).
- **Argument Hashing:** Tool arguments are hashed with SHA-256 before storage to protect confidential inputs by default.
- **Hash Chaining:** Record `N` includes `prev_hash` equal to the SHA-256 hash of Record `N-1`. The first record has `prev_hash = "genesis"`.
- **Signed Checkpoints:** Every 10 records, a Merkle root over the record hashes in the window is computed and signed with an Ed25519 private key.

## JSONL Trace Specification

Charter defines a standardized trace format for replaying and auditing agent execution runs.

Each line in a `.jsonl` trace file is a single JSON object:

```json
{
  "timestamp": "2026-11-13T10:00:00Z",
  "agent_id": "production-analyst-01",
  "tool": "query_database",
  "arguments": {
    "query": "SELECT count(*) FROM users"
  },
  "context": {
    "session_id": "sess-4821"
  },
  "autonomy_level": "medium"
}
```

### Fields

- `timestamp` (string, ISO 8601 UTC): When the agent initiated the tool call.
- `agent_id` (string): Unique identifier for the agent or role.
- `tool` (string): The tool or function name requested.
- `arguments` (object): Key-value arguments passed to the tool.
- `context` (object): Operational metadata (e.g. session ID, tenant ID).
- `autonomy_level` (string, enum: `"low"`, `"medium"`, `"high"`): Autonomy tier of the executing agent.
