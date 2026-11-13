"""Charter demo: mock agent with policy enforcement, ledger, and evidence report."""
from pathlib import Path
from charter.policy.schema import PolicyConfig, Rule, Condition
from charter.policy.evaluator import evaluate
from charter.ledger.store import LedgerStore
from charter.ledger.verify import verify_chain
from charter.evidence.catalog import ObligationCatalog
from charter.evidence.coverage import compute_coverage
from charter.report.generator import MarkdownReportGenerator


def main():
    config = PolicyConfig(rules=[
        Rule(id="allow-reads", effect="allow", conditions=[
            Condition(tool_matches="read_*", autonomy_level_in=["low", "medium", "high"])
        ]),
        Rule(id="deny-writes", effect="deny", conditions=[
            Condition(tool_matches="write_*")
        ]),
        Rule(id="approve-execute", effect="require_approval", conditions=[
            Condition(tool_matches="execute_*")
        ]),
    ])

    store = LedgerStore(":memory:")

    tool_calls = [
        ("read_file", {"path": "/data/report.txt"}, "low"),
        ("read_database", {"table": "users"}, "medium"),
        ("write_file", {"path": "/etc/passwd"}, "high"),
        ("write_config", {"key": "debug"}, "low"),
        ("execute_code", {"code": "print('hello')"}, "medium"),
    ]

    print("=== Charter Demo ===\n")
    from charter.policy.schema import PolicyRequest
    for tool, arguments, autonomy in tool_calls:
        req = PolicyRequest(agent_id="demo-agent", tool=tool, arguments=arguments, autonomy_level=autonomy)
        result = evaluate(req, config)
        store.append("demo-agent", tool, result.decision, result.reason, result.rule_id, arguments)
        print(f"  {tool:30s} -> {result.decision:20s} (rule: {result.rule_id})")

    print("\n=== Verifying ledger ===\n")
    verify_result = verify_chain(store)
    print(f"  Valid: {verify_result.valid}")
    if verify_result.errors:
        for e in verify_result.errors:
            print(f"  ERROR: {e}")

    print("\n=== Evidence Report ===\n")
    data_dir = Path(__file__).parent.parent / "data" / "obligations"
    catalog = ObligationCatalog()
    catalog.load_from_dir(data_dir)
    records = store.get_all()
    coverage = compute_coverage(catalog, records)
    gen = MarkdownReportGenerator()
    report = gen.generate(catalog, coverage)
    print(report[:1500])
    print("\nCharter demo complete.")


if __name__ == "__main__":
    main()
