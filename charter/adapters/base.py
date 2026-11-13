from typing import Protocol

from charter.policy.schema import PolicyRequest, PolicyResult


class AgentAdapter(Protocol):
    def decide(self, request: PolicyRequest) -> PolicyResult: ...
