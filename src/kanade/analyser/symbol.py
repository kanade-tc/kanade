from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from kanade.analyser.model.type import KnBaseType

TypeVariance = Literal[
    "convariant",
    "invariant",
    "contravariant",
]


@dataclass(frozen=True, eq=True)
class TypeSymbolSpec:
    name: str
    variance: TypeVariance = "invariant"
    bound: KnBaseType | None = None
    constraints: tuple[KnBaseType, ...] = ()
    default: None = None


# TODO: ParamSpec, TypeVarTuple, etc.

@dataclass(frozen=True, eq=True)
class TypeSymbol:
    spec: TypeSymbolSpec
    owner: Any | None = None  # TODO: proper type
