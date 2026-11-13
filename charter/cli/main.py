from __future__ import annotations

import json
from pathlib import Path

import typer
import yaml

app = typer.Typer(
    help="Charter: governance and assurance layer for autonomous AI agents."
)


@app.command()
def check(
    agent_id: str = typer.Option("unknown", help="Agent identifier"),
    tool: str = typer.Option(..., help="Tool name to check"),
    args: str = typer.Option("{}", help="Tool arguments as a JSON string"),
    policy_file: Path | None = typer.Option(None, help="Path to a YAML policy file"),
):
    """Evaluate a policy decision for a given tool call."""
    from charter.policy.evaluator import evaluate
    from charter.policy.schema import PolicyConfig, PolicyRequest

    if policy_file and policy_file.exists():
        with policy_file.open() as f:
            raw = yaml.safe_load(f)
        config = PolicyConfig.model_validate(raw)
    else:
        config = PolicyConfig(rules=[])

    arguments = json.loads(args)
    request = PolicyRequest(agent_id=agent_id, tool=tool, arguments=arguments)
    result = evaluate(request, config)
    typer.echo(f"Decision : {result.decision}")
    typer.echo(f"Rule     : {result.rule_id}")
    typer.echo(f"Reason   : {result.reason}")


@app.command()
def verify(
    db_path: Path = typer.Option(..., help="Path to Charter SQLite ledger database"),
):
    """Verify the integrity of a ledger database."""
    from charter.ledger.store import LedgerStore
    from charter.ledger.verify import verify_chain

    store = LedgerStore(db_path)
    result = verify_chain(store)
    store.close()
    if result.valid:
        typer.echo("Chain valid.")
    else:
        for err in result.errors:
            typer.echo(f"ERROR: {err}", err=True)
        raise typer.Exit(code=1)


@app.command()
def report(
    db_path: Path = typer.Option(..., help="Path to Charter SQLite ledger database"),
    format: str = typer.Option("json", help="Output format: md, html, or json"),
    out: Path | None = typer.Option(None, help="Optional output file path"),
):
    """Generate an evidence report from a ledger database."""
    from charter.evidence.catalog import ObligationCatalog
    from charter.evidence.coverage import compute_coverage
    from charter.ledger.store import LedgerStore
    from charter.report.generator import (
        HTMLReportGenerator,
        JSONReportGenerator,
        MarkdownReportGenerator,
    )

    store = LedgerStore(db_path)
    records = store.get_all()
    store.close()

    data_dir = Path(__file__).parent.parent.parent / "data" / "obligations"
    catalog = ObligationCatalog()
    if data_dir.exists():
        catalog.load_from_dir(data_dir)

    coverage = compute_coverage(catalog, records)

    if format == "md":
        content = MarkdownReportGenerator().generate(catalog, coverage)
    elif format == "html":
        content = HTMLReportGenerator().generate(catalog, coverage)
    else:
        content = JSONReportGenerator().generate(catalog, coverage)

    if out:
        out.write_text(content, encoding="utf-8")
        typer.echo(f"Report written to {out}")
    else:
        typer.echo(content)


@app.command()
def replay(
    trace: Path = typer.Option(..., help="Path to a JSONL trace file"),
    db_path: Path = typer.Option(..., help="Path to Charter SQLite ledger database"),
    policy_file: Path | None = typer.Option(
        None, help="Optional path to a YAML policy file"
    ),
):
    """Replay a JSONL trace file through the evaluator and log results."""
    from charter.ledger.store import LedgerStore
    from charter.policy.evaluator import evaluate
    from charter.policy.schema import PolicyConfig, PolicyRequest

    if policy_file and policy_file.exists():
        with policy_file.open() as f:
            raw = yaml.safe_load(f)
        config = PolicyConfig.model_validate(raw)
    else:
        config = PolicyConfig(rules=[])
    store = LedgerStore(db_path)

    with trace.open() as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            request = PolicyRequest(
                agent_id=entry.get("agent_id", "replay"),
                tool=entry.get("tool", "unknown"),
                arguments=entry.get("arguments", {}),
                autonomy_level=entry.get("autonomy_level", "low"),
            )
            result = evaluate(request, config)
            store.append(
                agent_id=request.agent_id,
                tool=request.tool,
                decision=result.decision,
                reason=result.reason,
                rule_id=result.rule_id,
                arguments=request.arguments,
            )
            typer.echo(f"Line {lineno}: {request.tool} -> {result.decision}")

    store.close()
    typer.echo("Replay complete.")


if __name__ == "__main__":
    app()
