from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, model_validator


class Condition(BaseModel):
    tool_matches: str | None = None
    autonomy_level_in: list[str] | None = None
    argument_contains: dict[str, Any] | None = None


class Rule(BaseModel):
    id: str
    effect: Literal["allow", "deny", "require_approval"]
    conditions: list[Condition] = []


class PolicyConfig(BaseModel):
    rules: list[Rule] = []
    default_effect: Literal["deny"] = "deny"

    @model_validator(mode="after")
    def _no_duplicate_ids(self) -> PolicyConfig:
        seen: set[str] = set()
        for r in self.rules:
            if r.id in seen:
                raise ValueError(f"Duplicate rule id: {r.id}")
            seen.add(r.id)
        return self


class PolicyRequest(BaseModel):
    agent_id: str
    tool: str
    arguments: dict[str, Any] = {}
    context: dict[str, Any] = {}
    autonomy_level: Literal["low", "medium", "high"] = "low"


class PolicyResult(BaseModel):
    decision: Literal["allow", "deny", "require_approval"]
    rule_id: str
    reason: str
    timestamp: datetime
