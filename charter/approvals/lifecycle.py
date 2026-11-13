from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Literal, Protocol

from pydantic import BaseModel


class ApprovalRequest(BaseModel):
    request_id: str
    agent_id: str
    tool: str
    arguments: dict
    timeout_seconds: float = 30.0


class ApprovalResult(BaseModel):
    request_id: str
    decision: Literal["approved", "denied", "timeout"]
    decided_at: datetime
    reason: str


class ApprovalChannel(Protocol):
    async def request_approval(self, req: ApprovalRequest) -> ApprovalResult: ...


class TimeoutApprovalChannel:
    """Times out after timeout_seconds and returns deny-equivalent result."""

    async def request_approval(self, req: ApprovalRequest) -> ApprovalResult:
        await asyncio.sleep(req.timeout_seconds)
        return ApprovalResult(
            request_id=req.request_id,
            decision="timeout",
            decided_at=datetime.now(UTC),
            reason="Approval timed out. Defaulting to deny.",
        )


class ImmediateApprovalChannel:
    """Immediately approves or denies. For testing."""

    def __init__(self, approve: bool = True) -> None:
        self.approve = approve

    async def request_approval(self, req: ApprovalRequest) -> ApprovalResult:
        return ApprovalResult(
            request_id=req.request_id,
            decision="approved" if self.approve else "denied",
            decided_at=datetime.now(UTC),
            reason="Immediate decision (testing channel).",
        )
