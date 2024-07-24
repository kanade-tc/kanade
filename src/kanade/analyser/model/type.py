from __future__ import annotations

from dataclasses import dataclass

from kanade.analyser.signature import TypedSignature
from kanade.analyser.symbol import TypeSymbolSpec, TypeSymbol
from kanade.analyser.utils import Singleton

LITERAL_TYPES = str | int | float | bool | None


@dataclass
class KnBaseType: ...


@dataclass
class KnAlias(KnBaseType):
    alias: KnBaseType


@dataclass
class KnType(KnBaseType): ...


@dataclass
class KnAny(KnType, metaclass=Singleton): ...


@dataclass
class KnNever(KnType, metaclass=Singleton): ...


@dataclass
class KnUnbounded(KnType, metaclass=Singleton): ...


@dataclass
class KnNone(KnType, metaclass=Singleton): ...


@dataclass
class KnEllipsis(KnType, metaclass=Singleton): ...


@dataclass
class KnUnknown(KnType, metaclass=Singleton): ...


@dataclass
class KnUnpack(KnType):
    target: KnBaseType


@dataclass
class KnVariable(KnType):
    symbol: TypeSymbol


@dataclass
class KnUnion(KnType):
    types: list[KnBaseType]


@dataclass
class KnIntersection(KnType):
    types: list[KnBaseType]


@dataclass
class KnTuple(KnType):
    types: list[KnBaseType]


@dataclass
class KnInstance(KnType):
    info: ...
    args: list[KnType]


@dataclass
class KnClassOf(KnType):
    type: KnBaseType


@dataclass
class KnProtocol(KnType): ...


@dataclass
class KnParameters(KnType): ...


@dataclass
class KnFunctionLike(KnType): ...


@dataclass
class KnCallable(KnFunctionLike):
    parameters: KnParameters
    return_type: KnBaseType

    @property
    def signature(self) -> TypedSignature: ...  # TODO


@dataclass
class KnOverloaded(KnFunctionLike):
    overloads: list[KnCallable]

    @property
    def signature(self) -> ...: ...  # TODO


@dataclass
class KnLiteral(KnType):
    value: LITERAL_TYPES
