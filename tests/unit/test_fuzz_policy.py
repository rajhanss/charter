import random

import pytest

from charter.policy.evaluator import evaluate
from charter.policy.schema import Condition, PolicyConfig, PolicyRequest, Rule

rng = random.Random(42)

TOOLS = ["read_file", "write_file", "execute_command", "send_email", "query_db"]
EFFECTS = ["allow", "deny", "require_approval"]
AUTONOMY_LEVELS = ["low", "medium", "high"]


def generate_random_condition():
    choice = rng.randint(0, 2)
    if choice == 0:
        return Condition(tool_matches=f"{rng.choice(TOOLS)[:4]}*")
    elif choice == 1:
        return Condition(
            autonomy_level_in=rng.sample(AUTONOMY_LEVELS, k=rng.randint(1, 2))
        )
    else:
        return Condition(argument_contains={"key": str(rng.randint(1, 5))})


def generate_random_policy(num_rules: int):
    rules = []
    for i in range(num_rules):
        conds = [generate_random_condition() for _ in range(rng.randint(0, 3))]
        rules.append(
            Rule(
                id=f"rule-{i}",
                effect=rng.choice(EFFECTS),
                conditions=conds,
            )
        )
    return PolicyConfig(rules=rules)


@pytest.mark.parametrize("iteration", range(50))
def test_fuzz_policy_evaluation_properties(iteration):
    policy = generate_random_policy(num_rules=rng.randint(1, 10))
    req = PolicyRequest(
        agent_id=f"agent-{rng.randint(1, 10)}",
        tool=rng.choice(TOOLS),
        arguments={"key": str(rng.randint(1, 5)), "other": rng.random()},
        autonomy_level=rng.choice(AUTONOMY_LEVELS),
    )

    result = evaluate(req, policy)

    # Invariants that must ALWAYS hold:
    assert result.decision in {"allow", "deny", "require_approval"}
    assert result.rule_id != ""
    assert result.timestamp is not None

    # Check deny precedence:
    # If any matching rule had effect="deny", result MUST be deny
    from charter.policy.evaluator import _rule_matches

    matching_rules = [r for r in policy.rules if _rule_matches(r, req)]
    if any(r.effect == "deny" for r in matching_rules):
        assert result.decision == "deny"
    elif not matching_rules:
        assert result.decision == "deny"
        assert result.rule_id == "default-deny"
