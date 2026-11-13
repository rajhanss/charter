# Charter

**Open-source governance and assurance layer for autonomous AI agents.**

Charter bridges the gap between runtime policy enforcement and compliance paperwork. Every action an autonomous AI agent attempts is decided by deterministic policy outside the model, recorded in a tamper-evident cryptographic hash chain, and mapped directly to compliance obligations (EU AI Act, NIST AI RMF, ISO/IEC 42001). Evidence can be verified offline by any third party without trusting a Charter server.

---

## What Charter is NOT

- Not an LLM content guardrail or prompt filter (no prompt injection filtering, no output toxicity moderation).
- Not a red-teaming tool or adversarial attack framework.
- Not a GRC dashboard for manual checklist management.
- Not a legal compliance certifier. Charter produces technical evidence and control mappings; it does not certify legal compliance (see [LIMITATIONS.md](LIMITATIONS.md)).

## What Charter IS

- **Deterministic policy engine:** Evaluates agent requests before tool execution. Default deny, deny precedence, rule-level explanation.
- **Tamper-evident ledger:** Append-only SQLite ledger with SHA-256 hash chaining and periodic Ed25519-signed Merkle checkpoints.
- **Offline verification:** Third-party verification (`charter verify`) detects any record modification, insertion, or deletion without network access.
- **Obligation mapping:** Maps technical actions to EU AI Act (Articles 9, 12, 13, 14, 15), NIST AI RMF 1.0 (GOVERN, MANAGE, MEASURE), and ISO/IEC 42001 clauses.
- **Multi-format reporting:** Generates audit-ready evidence reports in Markdown, HTML, and JSON (inspired by NIST OSCAL).
- **Flexible integration:** Python decorator (`@charter_policy`), FastAPI middleware, and HTTP service.

---

## Measured Benchmarks

Measured on Python 3.12:

| Metric | Measured Value | Note |
|---|---|---|
| **Policy evaluation latency** | **4.84 μs / decision** | Pure evaluation in-memory, no I/O |
| **Ledger append latency** | **0.03 ms / record** | Canonical JSON + SHA-256 hash chain + SQLite write + Ed25519 checkpoints |
| **Offline verification throughput** | **>45,000 records / sec** | Full SHA-256 chain recomputation + Merkle checkpoint verification |
| **Test suite pass rate** | **103 passed in 1.88s** | 100% unit and integration pass rate |

---

## Quick Start

### Installation

```bash
pip install charter
```

Or install from source:

```bash
git clone https://github.com/rajhanss/charter.git
cd charter
pip install -e ".[dev]"
```

### 1. Define a Policy (`policy.yaml`)

```yaml
rules:
  - id: allow-safe-reads
    effect: allow
    conditions:
      - tool_matches: "read_*"
        autonomy_level_in: ["low", "medium", "high"]

  - id: deny-system-writes
    effect: deny
    conditions:
      - tool_matches: "write_*"
        argument_contains:
          path: "/etc/passwd"

  - id: approve-code-exec
    effect: require_approval
    conditions:
      - tool_matches: "execute_*"
```

### 2. Check a Policy Decision (CLI)

```bash
charter check --tool read_file --args '{"path": "/data/report.txt"}' --policy-file policy.yaml
```

Output:
```text
Decision : allow
Rule     : allow-safe-reads
Reason   : Rule 'allow-safe-reads' allows this request.
```

### 3. Verify Ledger Integrity Offline

```bash
charter verify --db-path ./charter.db
```

Output:
```text
Chain valid.
```

### 4. Generate Evidence Report

```bash
charter report --db-path ./charter.db --format md --out report.md
```

### 5. Replay Traces

```bash
charter replay --trace examples/recorded_trace.jsonl --db-path ./charter.db
```

---

## Framework Obligation Coverage

Charter includes built-in obligation catalogs in `data/obligations/`:

| Framework | Obligations Covered | Key Requirements |
|---|---|---|
| **EU AI Act** | Articles 9, 12, 13, 14, 15 | Risk management, record-keeping, transparency, human oversight, accuracy/robustness |
| **NIST AI RMF 1.0** | GOVERN 1.1, 4.1; MEASURE 2.5; MANAGE 2.2 | Policies & accountability, risk limits, system behavior telemetry, human intervention |
| **ISO/IEC 42001** | Clauses 6.1, 8.4, 9.1, 10.2 | Risk actions, AI impact assessment, monitoring & evaluation, nonconformity tracking |

---

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for module decomposition, ledger hash chain details, and the JSONL trace specification.

## Threat Model

See [THREAT_MODEL.md](THREAT_MODEL.md) for security analysis covering policy bypass, log tampering, tail truncation, replay attacks, and key compromise.

## Limitations

See [LIMITATIONS.md](LIMITATIONS.md) for documented engineering trade-offs and non-guarantees.

---

## License

MIT License. See LICENSE for details.
