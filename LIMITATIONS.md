# Charter Limitations and Engineering Non-Guarantees

Charter is designed with explicit boundaries. This document specifies what Charter v0.1.0 does not guarantee.

## 1. No Legal Compliance Certification

Charter provides automated technical evidence and obligation mapping. It produces reports detailing what policy decisions occurred and how they relate to regulatory frameworks (EU AI Act, NIST AI RMF, ISO/IEC 42001).
Charter **does not certify legal compliance**, and using Charter does not grant regulatory immunity. All compliance decisions remain the responsibility of deployers and legal counsel.

## 2. Hash Chain Tail Truncation

A linear hash chain can detect:
- Any field modification within any record.
- Any record insertion between existing records.
- Any record deletion from the middle of the chain.

However, a bare hash chain **cannot detect truncation of the tail** (deleting the most recent records back to an earlier valid state) without an external anchor. To detect truncation, operators must anchor periodic checkpoint Merkle roots to an external source (such as a git tag, remote transparency service, or external audit log).

## 3. Local Key Management

In version 0.1.0, Ed25519 checkpoint signing keys are generated locally and stored in the database. Charter does not currently integrate with Hardware Security Modules (HSMs), AWS KMS, Google Cloud KMS, or HashiCorp Vault. Production deployments requiring FIPS-140-2 compliance must manage external key anchoring.

## 4. Policy Engine Language Scope

Charter v0.1.0 uses a native YAML and Pydantic policy format with glob matching and exact argument equality checks. It does not currently embed Open Policy Agent (Rego) or AWS Cedar evaluators, though the evaluation engine sits behind an interface designed to accommodate these engines in future releases.

## 5. Non-Sandboxing Model

Charter governs declared tool invocations. It does not enforce OS-level sandboxing, seccomp filters, or container network boundaries. If an agent process possesses direct hardware or socket access outside Charter's instrumented wrappers, Charter cannot intercept those actions.
