from __future__ import annotations

import functools

from charter.ledger.store import LedgerStore
from charter.policy.evaluator import evaluate
from charter.policy.schema import PolicyConfig, PolicyRequest


class PolicyDeniedError(Exception):
    pass


class ApprovalRequiredError(Exception):
    pass


def charter_policy(
    *, policy_config: PolicyConfig, ledger: LedgerStore, agent_id: str = "unknown"
):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            tool = fn.__name__
            arguments = kwargs
            req = PolicyRequest(agent_id=agent_id, tool=tool, arguments=arguments)
            result = evaluate(req, policy_config)
            ledger.append(
                agent_id=agent_id,
                tool=tool,
                decision=result.decision,
                reason=result.reason,
                rule_id=result.rule_id,
                arguments=arguments,
            )
            if result.decision == "deny":
                raise PolicyDeniedError(f"Tool {tool!r} denied: {result.reason}")
            if result.decision == "require_approval":
                raise ApprovalRequiredError(
                    f"Tool {tool!r} requires approval: {result.reason}"
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator
