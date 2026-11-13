"""Pure policy evaluator. No I/O, no global state."""

from __future__ import annotations

import fnmatch
from datetime import UTC, datetime

from .schema import Condition, PolicyConfig, PolicyRequest, PolicyResult, Rule


def _condition_matches(cond: Condition, req: PolicyRequest) -> bool:
    if cond.tool_matches is not None and not fnmatch.fnmatch(
        req.tool, cond.tool_matches
    ):
        return False
    if (
        cond.autonomy_level_in is not None
        and req.autonomy_level not in cond.autonomy_level_in
    ):
        return False
    if cond.argument_contains is not None:
        for k, v in cond.argument_contains.items():
            if req.arguments.get(k) != v:
                return False
    return True


def _rule_matches(rule: Rule, req: PolicyRequest) -> bool:
    if not rule.conditions:
        return True
    return all(_condition_matches(c, req) for c in rule.conditions)


def evaluate(request: PolicyRequest, config: PolicyConfig) -> PolicyResult:
    matching: list[Rule] = [r for r in config.rules if _rule_matches(r, request)]
    ts = datetime.now(UTC)

    # deny beats everything
    for rule in matching:
        if rule.effect == "deny":
            return PolicyResult(
                decision="deny",
                rule_id=rule.id,
                reason=f"Rule {rule.id!r} explicitly denies this request.",
                timestamp=ts,
            )

    for rule in matching:
        if rule.effect == "require_approval":
            return PolicyResult(
                decision="require_approval",
                rule_id=rule.id,
                reason=f"Rule {rule.id!r} requires human approval.",
                timestamp=ts,
            )

    for rule in matching:
        if rule.effect == "allow":
            return PolicyResult(
                decision="allow",
                rule_id=rule.id,
                reason=f"Rule {rule.id!r} allows this request.",
                timestamp=ts,
            )

    return PolicyResult(
        decision="deny",
        rule_id="default-deny",
        reason="No matching rule found. Default policy is deny.",
        timestamp=ts,
    )
