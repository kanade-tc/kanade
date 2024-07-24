from __future__ import annotations

from dataclasses import dataclass

from kanade.analyser.signature import TypedSignature
from kanade.analyser.symbol import TypeSymbolSpec
from kanade.analyser.utils import Singleton

LITERAL_TYPES = str | int | float | bool | None


@dataclass
class KnBaseType: ...


@dataclass
class KnAlias(KnBaseType):
    alias: KnBaseType


@dataclass
class KnAny(KnBaseType, metaclass=Singleton): ...


@dataclass
class KnNever(KnBaseType, metaclass=Singleton): ...


@dataclass
class KnUnbounded(KnBaseType, metaclass=Singleton): ...


@dataclass
class KnType(KnBaseType): ...


@dataclass
class KnUnpack(KnBaseType):
    target: KnBaseType


@dataclass
class KnVariable(KnBaseType):
    symbol: TypeSymbolSpec


@dataclass
class KnNone(KnType, metaclass=Singleton): ...


@dataclass
class KnEllipsis(KnType, metaclass=Singleton): ...


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
class KnProtocol(KnBaseType): ...


@dataclass
class KnParameters(KnType): ...


@dataclass
class KnFunctionLike(KnType): ...


@dataclass
class KnCallable(KnFunctionLike):
    parameters: KnParameters
    return_type: KnBaseType

    @property
    def signature(self) -> TypedSignature:
        ...  # TODO

@dataclass
class KnOverloaded(KnFunctionLike):
    overloads: list[KnCallable]

    @property
    def signature(self) -> ...: ...  # TODO


@dataclass
class KnLiteral(KnFunctionLike):
    value: LITERAL_TYPES
