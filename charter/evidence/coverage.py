from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from charter.ledger.models import LedgerRecord

from .catalog import ObligationCatalog


@dataclass
class ControlCoverage:
    obligation_id: str
    status: Literal["evidenced", "partial", "no_evidence"]
    record_count: int
    example_hashes: list[str]


def _run_query(query: dict, records: list[LedgerRecord]) -> list[LedgerRecord]:
    if query.get("type") == "ledger_count":
        filt = query.get("filter", {})
        matched = []
        for r in records:
            if all(getattr(r, k, None) == v for k, v in filt.items()):
                matched.append(r)
        return matched
    return []


def compute_coverage(
    catalog: ObligationCatalog, records: list[LedgerRecord]
) -> list[ControlCoverage]:
    results = []
    for ob in catalog.all():
        passing = 0
        total = len(ob.evidence_queries)
        all_matched: list[LedgerRecord] = []
        for q in ob.evidence_queries:
            matched = _run_query(q, records)
            min_count = q.get("min_count", 1)
            if len(matched) >= min_count:
                passing += 1
            all_matched.extend(matched)

        if total == 0:
            status: Literal["evidenced", "partial", "no_evidence"] = "no_evidence"
        elif passing == total:
            status = "evidenced"
        elif passing > 0:
            status = "partial"
        else:
            status = "no_evidence"

        example_hashes = list({r.record_hash for r in all_matched})[:3]
        results.append(
            ControlCoverage(
                obligation_id=ob.id,
                status=status,
                record_count=len(all_matched),
                example_hashes=example_hashes,
            )
        )
    return results
