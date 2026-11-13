from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Obligation:
    id: str
    framework: str
    reference: str
    title: str
    description: str
    technical_controls: list[str] = field(default_factory=list)
    evidence_queries: list[dict] = field(default_factory=list)


class ObligationCatalog:
    def __init__(self) -> None:
        self._obligations: list[Obligation] = []

    def load_from_dir(self, path: Path) -> None:
        for yaml_file in sorted(path.glob("*.yaml")):
            with yaml_file.open() as f:
                items = yaml.safe_load(f) or []
            for item in items:
                self._obligations.append(Obligation(**item))

    def all(self) -> list[Obligation]:
        return list(self._obligations)

    def by_framework(self, framework: str) -> list[Obligation]:
        return [o for o in self._obligations if o.framework == framework]
