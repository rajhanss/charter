import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from charter.adapters.decorator import (
    ApprovalRequiredError,
    PolicyDeniedError,
    charter_policy,
)
from charter.adapters.middleware import CharterMiddleware
from charter.ledger.store import LedgerStore
from charter.policy.schema import Condition, PolicyConfig, Rule


def test_decorator_allows_permitted_tool():
    config = PolicyConfig(
        rules=[
            Rule(
                id="r-allow",
                effect="allow",
                conditions=[Condition(tool_matches="read_data")],
            ),
        ]
    )
    store = LedgerStore(":memory:")

    @charter_policy(policy_config=config, ledger=store, agent_id="agent-01")
    def read_data(filename: str):
        return f"content of {filename}"

    result = read_data(filename="doc.txt")
    assert result == "content of doc.txt"
    records = store.get_all()
    assert len(records) == 1
    assert records[0].decision == "allow"
    assert records[0].tool == "read_data"


def test_decorator_raises_on_denied_tool():
    config = PolicyConfig(
        rules=[
            Rule(
                id="r-deny",
                effect="deny",
                conditions=[Condition(tool_matches="delete_data")],
            ),
        ]
    )
    store = LedgerStore(":memory:")

    @charter_policy(policy_config=config, ledger=store, agent_id="agent-01")
    def delete_data(filename: str):
        return "deleted"

    with pytest.raises(PolicyDeniedError) as exc_info:
        delete_data(filename="doc.txt")
    assert "denied" in str(exc_info.value).lower()

    records = store.get_all()
    assert len(records) == 1
    assert records[0].decision == "deny"


def test_decorator_raises_on_approval_required():
    config = PolicyConfig(
        rules=[
            Rule(
                id="r-appr",
                effect="require_approval",
                conditions=[Condition(tool_matches="deploy")],
            ),
        ]
    )
    store = LedgerStore(":memory:")

    @charter_policy(policy_config=config, ledger=store, agent_id="agent-01")
    def deploy(env: str):
        return "deployed"

    with pytest.raises(ApprovalRequiredError):
        deploy(env="prod")

    records = store.get_all()
    assert len(records) == 1
    assert records[0].decision == "require_approval"


@pytest.mark.asyncio
async def test_middleware_enforces_policy():
    config = PolicyConfig(
        rules=[
            Rule(
                id="r-api-allow",
                effect="allow",
                conditions=[Condition(tool_matches="/public/*")],
            ),
            Rule(
                id="r-api-deny",
                effect="deny",
                conditions=[Condition(tool_matches="/admin/*")],
            ),
        ]
    )
    store = LedgerStore(":memory:")

    test_app = FastAPI()
    test_app.add_middleware(CharterMiddleware, policy_config=config, ledger=store)

    @test_app.get("/public/info")
    async def public_info():
        return {"data": "public"}

    @test_app.get("/admin/secrets")
    async def admin_secrets():
        return {"data": "secret"}

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as ac:
        res_ok = await ac.get("/public/info")
        assert res_ok.status_code == 200

        res_deny = await ac.get("/admin/secrets")
        assert res_deny.status_code == 403

    records = store.get_all()
    assert len(records) == 2
    assert records[0].decision == "allow"
    assert records[1].decision == "deny"
