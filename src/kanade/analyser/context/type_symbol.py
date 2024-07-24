from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from kanade.analyser.model.type import KnType

@dataclass
class TypeSymbolContext:
    values: ... = field(default_factory=lambda: ...)

    assuming: list[tuple[KnType, Any]] = field(default_factory=list)

    @contextmanager
    def assume(self, left: KnType, right: KnType):
        self.assuming.append((left, right))
        try:
            yield
        finally:
            self.assuming.pop()
