# Charter Threat Model

This document outlines the threat model for Charter v0.1.0 in accordance with standard cryptographic and system security principles.

## 1. System Scope and Trust Boundaries

- **In Scope:** Policy evaluator, SQLite ledger store, SHA-256 hash chaining, Ed25519 checkpoint signing, offline verification (`charter verify`), and evidence compilation.
- **Out of Scope:** The agent's runtime environment, host OS security, hardware isolation, LLM prompt security, and legal certification.

## 2. Threats and Defenses

### 2.1 Policy Bypass

- **Threat:** An autonomous agent or adversarial prompt attempts to bypass policy evaluation and execute an unapproved tool call.
- **Defense:** Policy enforcement occurs strictly outside the model process in the runtime harness (via Python decorator, API gateway, or middleware). The model has no write access to policy rules or evaluator state. Default policy is `deny`.

### 2.2 Ledger Tampering (Modification, Insertion, Deletion)

- **Threat:** An attacker or malicious administrator modifies records in the SQLite database to hide unauthorized actions or forge approvals.
- **Defense:** Every record contains the SHA-256 hash of canonical JSON of its contents and points to the previous record's hash (`prev_hash`). Any modification of a field, insertion of an unchained record, or deletion of an intermediate record breaks the cryptographic link and is immediately detected by `charter verify`.
- **Periodic Checkpoints:** Every 10 records, a Merkle root over the record hashes is signed using an Ed25519 private key. Even if an attacker attempts to rewrite the entire hash chain from scratch, they cannot forge the Ed25519 signature without the private key.

### 2.3 Tail Truncation

- **Threat:** An attacker deletes the most recent $N$ records since the last checkpoint, making it appear that those actions never occurred.
- **Limitation & Mitigation:** A bare hash chain cannot detect tail truncation without an external anchor. Charter explicitly documents this limitation.
- **Mitigation Strategy:** Operators should anchor the latest checkpoint Merkle root outside the database (e.g. in an external transparency log, a signed git tag, or a remote append-only service). `charter verify` can then compare the local head against the external anchor.

### 2.4 Replay Attacks

- **Threat:** An attacker intercepts an `allow` decision and replays it to authorize an identical tool call at a later time.
- **Defense:** Decisions are tied to distinct `timestamp` values and contextual request hashes. State changes must go through the policy evaluator for each distinct invocation.

### 2.5 Key Compromise

- **Threat:** The private Ed25519 signing key used for checkpoints is compromised.
- **Defense:** Checkpoint verification stores public keys per checkpoint. In the event of key compromise, new keypairs can be provisioned. Historical checkpoints created before the compromise timestamp remain provable under earlier trusted key roots. Private keys are never stored in plain configuration or committed to version control.

## 3. What Charter Does NOT Protect Against

1. **Compromised Host / Root Access:** An attacker with root OS access can delete the entire database file or terminate the Charter process.
2. **Out-of-Band Tool Execution:** If the agent has direct network or OS access bypassing the Charter wrapper, Charter cannot observe or enforce policies on those out-of-band actions.
3. **Flawed Policy Authoring:** If an administrator writes a rule that inadvertently allows dangerous tools (e.g. `tool_matches: "*"`), Charter will faithfully execute that rule.
4. **Legal Compliance Guarantees:** Charter records technical evidence of policy execution. It does not certify that an organization is legally compliant with the EU AI Act or other statutory regulations.
