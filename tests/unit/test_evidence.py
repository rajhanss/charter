from pathlib import Path

import pytest

from charter.evidence.catalog import ObligationCatalog
from charter.evidence.coverage import compute_coverage


@pytest.fixture
def data_dir():
    return Path(__file__).parent.parent.parent / "data" / "obligations"


def test_catalog_loads_all_frameworks(data_dir):
    catalog = ObligationCatalog()
    catalog.load_from_dir(data_dir)
    obs = catalog.all()
    assert len(obs) >= 10

    frameworks = {o.framework for o in obs}
    assert "EU AI Act" in frameworks
    assert "NIST AI RMF" in frameworks
    assert "ISO/IEC 42001" in frameworks


def test_every_obligation_has_evidence_queries(data_dir):
    catalog = ObligationCatalog()
    catalog.load_from_dir(data_dir)
    for ob in catalog.all():
        assert len(ob.evidence_queries) > 0, f"{ob.id} missing evidence queries"


def test_compute_coverage_empty_ledger(data_dir):
    catalog = ObligationCatalog()
    catalog.load_from_dir(data_dir)
    coverage = compute_coverage(catalog, [])
    assert len(coverage) == len(catalog.all())
    for c in coverage:
        assert c.status == "no_evidence"
        assert c.record_count == 0


def test_compute_coverage_with_matching_records(data_dir, mem_store):
    catalog = ObligationCatalog()
    catalog.load_from_dir(data_dir)

    # Log enough decisions to satisfy queries
    mem_store.append("a1", "write_file", "deny", "blocked by policy", "deny-rule", {})
    mem_store.append(
        "a1", "exec_tool", "require_approval", "manual approval", "appr-rule", {}
    )
    for i in range(6):
        mem_store.append(
            "a1", f"read_data_{i}", "allow", "authorized", "allow-rule", {}
        )

    records = mem_store.get_all()
    coverage = compute_coverage(catalog, records)

    cov_map = {c.obligation_id: c for c in coverage}
    # Article 9 has a query for deny records -> should be evidenced
    assert cov_map["euaia-art-9"].status == "evidenced"
    assert cov_map["euaia-art-9"].record_count >= 1

    # Article 14 has a query for require_approval -> should be evidenced
    assert cov_map["euaia-art-14"].status == "evidenced"
