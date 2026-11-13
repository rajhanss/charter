import pytest

from charter.approvals.lifecycle import (
    ApprovalRequest,
    ImmediateApprovalChannel,
    TimeoutApprovalChannel,
)


@pytest.mark.asyncio
async def test_timeout_produces_timeout_decision():
    channel = TimeoutApprovalChannel()
    req = ApprovalRequest(
        request_id="req-1",
        agent_id="agent-test",
        tool="deploy_prod",
        arguments={},
        timeout_seconds=0.01,
    )
    result = await channel.request_approval(req)
    assert result.decision == "timeout"
    assert "timed out" in result.reason.lower()


@pytest.mark.asyncio
async def test_immediate_approve():
    channel = ImmediateApprovalChannel(approve=True)
    req = ApprovalRequest(
        request_id="req-2",
        agent_id="agent-test",
        tool="read_db",
        arguments={},
    )
    result = await channel.request_approval(req)
    assert result.decision == "approved"


@pytest.mark.asyncio
async def test_immediate_deny():
    channel = ImmediateApprovalChannel(approve=False)
    req = ApprovalRequest(
        request_id="req-3",
        agent_id="agent-test",
        tool="rm_rf",
        arguments={},
    )
    result = await channel.request_approval(req)
    assert result.decision == "denied"
