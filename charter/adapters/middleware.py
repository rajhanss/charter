from __future__ import annotations

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from charter.ledger.store import LedgerStore
from charter.policy.evaluator import evaluate
from charter.policy.schema import PolicyConfig, PolicyRequest


class CharterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, policy_config: PolicyConfig, ledger: LedgerStore) -> None:
        super().__init__(app)
        self.policy_config = policy_config
        self.ledger = ledger

    async def dispatch(self, request: Request, call_next):
        agent_id = request.headers.get("X-Agent-Id", "unknown")
        tool = request.headers.get("X-Tool", request.url.path)
        req = PolicyRequest(agent_id=agent_id, tool=tool)
        result = evaluate(req, self.policy_config)
        self.ledger.append(
            agent_id=agent_id,
            tool=tool,
            decision=result.decision,
            reason=result.reason,
            rule_id=result.rule_id,
            arguments={},
        )
        if result.decision == "deny":
            return Response(
                content='{"detail":"denied"}',
                status_code=403,
                media_type="application/json",
            )
        return await call_next(request)
