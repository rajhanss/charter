from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from charter.evidence.catalog import ObligationCatalog
    from charter.evidence.coverage import ControlCoverage

DISCLAIMER = (
    "This report describes technical evidence recorded by Charter. "
    "It does not constitute legal compliance certification."
)


class MarkdownReportGenerator:
    def generate(
        self, catalog: ObligationCatalog, coverage: list[ControlCoverage]
    ) -> str:
        cov_map = {c.obligation_id: c for c in coverage}
        lines = [
            "# Charter Evidence Report",
            "",
            f"> **Disclaimer:** {DISCLAIMER}",
            "",
            "| Obligation | Framework | Reference | Status | Records | Example Hash |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for ob in catalog.all():
            cov = cov_map.get(ob.id)
            status = cov.status if cov else "no_evidence"
            records = cov.record_count if cov else 0
            example = (
                cov.example_hashes[0][:12] + "..." if cov and cov.example_hashes else ""
            )
            lines.append(
                f"| {ob.title} | {ob.framework} | {ob.reference} | {status} | {records} | {example} |"
            )
        lines.append("")
        lines.append(f"*Generated at {datetime.now(UTC).isoformat()}*")
        return "\n".join(lines)


class HTMLReportGenerator:
    STATUS_COLORS: ClassVar[dict[str, str]] = {
        "evidenced": "#c8e6c9",
        "partial": "#fff9c4",
        "no_evidence": "#ffcdd2",
    }

    def generate(
        self, catalog: ObligationCatalog, coverage: list[ControlCoverage]
    ) -> str:
        cov_map = {c.obligation_id: c for c in coverage}
        rows = []
        for ob in catalog.all():
            cov = cov_map.get(ob.id)
            status = cov.status if cov else "no_evidence"
            records = cov.record_count if cov else 0
            example = (
                cov.example_hashes[0][:12] + "..." if cov and cov.example_hashes else ""
            )
            color = self.STATUS_COLORS.get(status, "#ffffff")
            rows.append(
                f"<tr><td>{ob.title}</td><td>{ob.framework}</td><td>{ob.reference}</td>"
                f'<td style="background:{color}">{status}</td>'
                f"<td>{records}</td><td>{example}</td></tr>"
            )
        rows_html = "\n".join(rows)
        ts = datetime.now(UTC).isoformat()
        return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Charter Evidence Report</title></head>
<body style="font-family:sans-serif;max-width:900px;margin:2em auto">
<h1>Charter Evidence Report</h1>
<p style="border:1px solid #ccc;padding:1em;background:#f9f9f9"><em>{DISCLAIMER}</em></p>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
<thead><tr>
<th>Obligation</th><th>Framework</th><th>Reference</th>
<th>Status</th><th>Records</th><th>Example Hash</th>
</tr></thead>
<tbody>
{rows_html}
</tbody>
</table>
<p><small>Generated at {ts}</small></p>
</body>
</html>"""


class JSONReportGenerator:
    def generate(
        self, catalog: ObligationCatalog, coverage: list[ControlCoverage]
    ) -> str:
        cov_map = {c.obligation_id: c for c in coverage}
        controls = []
        for ob in catalog.all():
            cov = cov_map.get(ob.id)
            controls.append(
                {
                    "obligation_id": ob.id,
                    "framework": ob.framework,
                    "reference": ob.reference,
                    "title": ob.title,
                    "status": cov.status if cov else "no_evidence",
                    "record_count": cov.record_count if cov else 0,
                    "example_hashes": cov.example_hashes if cov else [],
                }
            )
        report = {
            "metadata": {
                "title": "Charter Evidence Report",
                "version": "0.1.0",
                "generated_at": datetime.now(UTC).isoformat(),
            },
            "disclaimer": DISCLAIMER,
            "controls": controls,
        }
        return json.dumps(report, indent=2)
