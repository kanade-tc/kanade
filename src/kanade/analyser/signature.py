from __future__ import annotations

from dataclasses import dataclass, field

from typing import TYPE_CHECKING

from kanade.language.python import PyExp

if TYPE_CHECKING:
    from kanade.analyser.model.type import KnBaseType

@dataclass
class TypedParameter:
    name: str
    type: KnBaseType | None = None
    default: PyExp | None = None


@dataclass
class TypedSignature:
    parameters: list[TypedParameter]
    return_type: KnBaseType
