from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, eq=True)
class TypeSymbolSpec:
    name: str
    