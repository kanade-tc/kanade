from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Parameter, Value, ParameterType


class SignatureErr: ...


@dataclass
class SignatureErrorGroup(Exception):
    errors: list[SignatureErr]


@dataclass
class TooManyPositionalArguments(SignatureErr):
    unconsumed: tuple[Value, ...]


@dataclass
class PositionalAssignForKeyword(SignatureErr):
    parameter: Parameter
    argument: Value


@dataclass
class ParameterAlreadyAssigned(SignatureErr):
    parameter: Parameter
    existing: Value
    argument: Value


@dataclass
class KeywordAssignForPositional(SignatureErr):
    parameter: Parameter
    argument: Value


@dataclass
class KeywordParameterNotFound(SignatureErr):
    name: str
    value: Value


@dataclass
class MissingRequredParameter(SignatureErr):
    parameter: Parameter


@dataclass
class DuplicatedParameterName(SignatureErr):
    name: str
    parameters: list[Parameter]


@dataclass
class MultiplePositionalVariablesParameter(SignatureErr):
    parameters: list[Parameter]


@dataclass
class MultipleKeywordVariablesParameter(SignatureErr):
    parameters: list[Parameter]


@dataclass
class ParameterMisplaced(SignatureErr):
    after: ParameterType
    parameter: Parameter
