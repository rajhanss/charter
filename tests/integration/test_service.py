import pytest
from httpx import ASGITransport, AsyncClient

from charter.service.routes import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "charter"


@pytest.mark.asyncio
async def test_decide_endpoint_default_deny():
    payload = {
        "agent_id": "test-agent",
        "tool": "delete_all",
        "arguments": {"target": "*"},
        "autonomy_level": "medium",
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.post("/decide", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "deny"
    assert data["rule_id"] == "default-deny"


@pytest.mark.asyncio
async def test_verify_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.get("/verify")
    assert res.status_code == 200
    data = res.json()
    assert "valid" in data
    assert "errors" in data


@pytest.mark.asyncio
async def test_report_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.get("/report?format=json")
    assert res.status_code == 200
