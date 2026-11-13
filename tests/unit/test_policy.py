import pytest
from pydantic import ValidationError

from charter.policy.evaluator import evaluate
from charter.policy.schema import Condition, PolicyConfig, PolicyRequest, Rule


def test_default_deny(empty_config):
    req = PolicyRequest(agent_id="agent-1", tool="any_tool")
    res = evaluate(req, empty_config)
    assert res.decision == "deny"
    assert res.rule_id == "default-deny"
    assert "default policy is deny" in res.reason.lower()


def test_explicit_allow_rule(allow_read_config):
    req = PolicyRequest(agent_id="agent-1", tool="read_file")
    res = evaluate(req, allow_read_config)
    assert res.decision == "allow"
    assert res.rule_id == "allow-read"


def test_deny_beats_allow():
    config = PolicyConfig(
        rules=[
            Rule(
                id="allow-read",
                effect="allow",
                conditions=[Condition(tool_matches="read_*")],
            ),
            Rule(
                id="deny-secret",
                effect="deny",
                conditions=[Condition(tool_matches="read_secret")],
            ),
        ]
    )
    req = PolicyRequest(agent_id="agent-1", tool="read_secret")
    res = evaluate(req, config)
    assert res.decision == "deny"
    assert res.rule_id == "deny-secret"


def test_require_approval_fires():
    config = PolicyConfig(
        rules=[
            Rule(
                id="approve-exec",
                effect="require_approval",
                conditions=[Condition(tool_matches="exec_*")],
            ),
        ]
    )
    req = PolicyRequest(agent_id="agent-1", tool="exec_command")
    res = evaluate(req, config)
    assert res.decision == "require_approval"
    assert res.rule_id == "approve-exec"


def test_malformed_rule_rejected_duplicate_ids():
    with pytest.raises(ValidationError):
        PolicyConfig(
            rules=[
                Rule(id="rule-1", effect="allow"),
                Rule(id="rule-1", effect="deny"),
            ]
        )


def test_rule_id_always_present():
    config = PolicyConfig(
        rules=[
            Rule(
                id="allow-test",
                effect="allow",
                conditions=[Condition(tool_matches="test")],
            ),
        ]
    )
    req1 = PolicyRequest(agent_id="a1", tool="test")
    assert evaluate(req1, config).rule_id == "allow-test"

    req2 = PolicyRequest(agent_id="a1", tool="other")
    assert evaluate(req2, config).rule_id == "default-deny"


def test_autonomy_level_in_condition():
    config = PolicyConfig(
        rules=[
            Rule(
                id="low-autonomy-only",
                effect="allow",
                conditions=[Condition(tool_matches="run_*", autonomy_level_in=["low"])],
            ),
        ]
    )
    req_low = PolicyRequest(agent_id="a1", tool="run_job", autonomy_level="low")
    assert evaluate(req_low, config).decision == "allow"

    req_high = PolicyRequest(agent_id="a1", tool="run_job", autonomy_level="high")
    assert evaluate(req_high, config).decision == "deny"


def test_argument_contains_condition():
    config = PolicyConfig(
        rules=[
            Rule(
                id="deny-critical-path",
                effect="deny",
                conditions=[
                    Condition(
                        tool_matches="write_file",
                        argument_contains={"path": "/etc/shadow"},
                    )
                ],
            ),
            Rule(
                id="allow-write",
                effect="allow",
                conditions=[Condition(tool_matches="write_file")],
            ),
        ]
    )
    req_shadow = PolicyRequest(
        agent_id="a1", tool="write_file", arguments={"path": "/etc/shadow"}
    )
    assert evaluate(req_shadow, config).decision == "deny"

    req_temp = PolicyRequest(
        agent_id="a1", tool="write_file", arguments={"path": "/tmp/test.txt"}
    )
    assert evaluate(req_temp, config).decision == "allow"
