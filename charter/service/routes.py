from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from charter import __version__
from charter.evidence.catalog import ObligationCatalog
from charter.evidence.coverage import compute_coverage
from charter.ledger.store import LedgerStore
from charter.ledger.verify import verify_chain
from charter.policy.evaluator import evaluate
from charter.policy.schema import PolicyConfig, PolicyRequest, PolicyResult
from charter.report.generator import (
    HTMLReportGenerator,
    JSONReportGenerator,
    MarkdownReportGenerator,
)

_ledger = LedgerStore(":memory:")
_policy_config = PolicyConfig(rules=[])

_catalog = ObligationCatalog()
_data_dir = Path(__file__).parent.parent.parent / "data" / "obligations"
if _data_dir.exists():
    _catalog.load_from_dir(_data_dir)

app = FastAPI(title="Charter", version=__version__)


@app.get("/health")
async def health():
    return {"status": "ok", "version": __version__, "service": "charter"}


@app.post("/decide", response_model=PolicyResult)
async def decide(request: PolicyRequest):
    result = evaluate(request, _policy_config)
    _ledger.append(
        agent_id=request.agent_id,
        tool=request.tool,
        decision=result.decision,
        reason=result.reason,
        rule_id=result.rule_id,
        arguments=request.arguments,
    )
    return result


@app.get("/verify")
async def verify():
    result = verify_chain(_ledger)
    return {"valid": result.valid, "errors": result.errors}


@app.get("/report")
async def report(format: str = Query(default="json", pattern="^(md|html|json)$")):
    records = _ledger.get_all()
    coverage = compute_coverage(_catalog, records)
    if format == "md":
        content = MarkdownReportGenerator().generate(_catalog, coverage)
        return PlainTextResponse(content, media_type="text/markdown")
    elif format == "html":
        content = HTMLReportGenerator().generate(_catalog, coverage)
        return HTMLResponse(content)
    else:
        content = JSONReportGenerator().generate(_catalog, coverage)
        return JSONResponse(content={"report": content})
