import pytest

from charter.ledger.store import LedgerStore
from charter.policy.schema import Condition, PolicyConfig, Rule


@pytest.fixture
def empty_config():
    return PolicyConfig(rules=[])


@pytest.fixture
def allow_read_config():
    return PolicyConfig(
        rules=[
            Rule(
                id="allow-read",
                effect="allow",
                conditions=[Condition(tool_matches="read_*")],
            ),
        ]
    )


@pytest.fixture
def mem_store():
    return LedgerStore(":memory:")
