from __future__ import annotations

from dataclasses import dataclass, field
from itertools import groupby
from typing import Any, Literal
from inspect import Signature as RuntimeSignature, Parameter as RuntimeParameter, _ParameterKind

from kanade.signature_prototype.error import (
    DuplicatedParameterName,
    KeywordAssignForPositional,
    KeywordParameterNotFound,
    MissingRequredParameter,
    MultipleKeywordVariablesParameter,
    MultiplePositionalVariablesParameter,
    ParameterAlreadyAssigned,
    ParameterMisplaced,
    PositionalAssignForKeyword,
    SignatureErrorGroup,
    TooManyPositionalArguments,
)

Value = Any  # TODO: Replace with a proper type
ParameterType = Literal["position-only", "keyword-only", "position-variables", "keyword-variables", "positional-or-keyword"]
PARAMETER_TYPES_PRIORITY = {
    "position-only": 0,
    "positional-or-keyword": 1,
    "position-variables": 2,
    "keyword-only": 3,
    "keyword-variables": 4,
}
PARAMETER_TYPES_CAST_MAP: dict[_ParameterKind, ParameterType] = {
    RuntimeParameter.POSITIONAL_ONLY: "position-only",
    RuntimeParameter.POSITIONAL_OR_KEYWORD: "positional-or-keyword",
    RuntimeParameter.VAR_POSITIONAL: "position-variables",
    RuntimeParameter.KEYWORD_ONLY: "keyword-only",
    RuntimeParameter.VAR_KEYWORD: "keyword-variables",
}


@dataclass(eq=True, frozen=True)  # TODO: implement ordering for get_proper_signature
class Parameter:
    """
    A parameter in a signature.
    
    Attributes:
        name (str): The name of the parameter.
        annotation (Value | None): The annotation of the parameter.
        default (Value | None): The default value of the parameter.
        type (ParameterType): The type of the parameter.
        
    """

    name: str

    annotation: Value | None = None
    default: Value | None = None

    type: ParameterType = "positional-or-keyword"

    def __str__(self):
        """
        Return the string representation of the parameter.
        
        Returns:
            str: The string representation.
        """

        if self.type == "position-variables":
            prefix = "*"
        elif self.type == "keyword-variables":
            prefix = "**"
        else:
            prefix = ""

        if self.annotation is not None:
            annotation = f": {self.annotation}"
        else:
            annotation = ""

        if self.default is not None:
            default = f" = {self.default}"
        else:
            default = ""

        return f"{prefix}{self.name}{annotation}{default}"

    def __lt__(self, other):
        """
        Compare the parameter with another parameter.
        Result is based on the priority of the parameter types which follow python rules.
        
        Args:
            other (Parameter): The other parameter.
        """

        if not isinstance(other, Parameter):
            return NotImplemented

        return PARAMETER_TYPES_PRIORITY[self.type] < PARAMETER_TYPES_PRIORITY[other.type]


@dataclass
class BindOptions:
    """
    Options for binding a signature.

    Attributes:
        reassignable (bool | dict[str, bool]): Specifies whether the signature is reassignable.
            If `reassignable` is a boolean, it applies to all parameters.
            If `reassignable` is a dictionary, it specifies the reassignability of individual parameters.
            Defaults to False.
    """

    reassignable: bool | dict[str, bool] = False


@dataclass
class BindResult:
    """
    Represents the result of binding a signature with arguments.

    Attributes:
        signature (Signature): The signature that was bound.
        last_parameters (list[Parameter]): The remaining parameters after binding.
        bounded_args (dict[str, Value | list[Value] | dict[str, Value]]): The bound arguments.
        completed (bool): Indicates if the binding process is completed.
        options (BindOptions): The options for the binding process.
    """

    signautre: Signature
    last_parameters: list[Parameter] = field(default_factory=list)
    bounded_args: dict[str, Value | list[Value] | dict[str, Value]] = field(default_factory=dict)
    completed: bool = False

    _options: BindOptions = field(default_factory=BindOptions)

    def cbind_partial(self, args: tuple[Value, ...], kwargs: dict[str, Value]):
        """
        Bind the signature with partial arguments.

        Args:
            args (tuple[Value, ...]): Positional arguments.
            kwargs (dict[str, Value]): Keyword arguments.

        Returns:
            BindResult: The bind result.

        Raises:
            SignatureErrorGroup: If there are errors in binding.
        """
        errors = []
        next_parameters = self.last_parameters.copy()
        bounded_args = self.bounded_args.copy()

        for ix, positional_arg in enumerate(args):
            if not next_parameters:
                errors.append(TooManyPositionalArguments(unconsumed=args[ix:]))  # TODO: add more info
                break

            param = next_parameters.pop(0)  # TODO: reassign support
            if param.type in ["keyword-only", "keyword-variables"]:
                # find *args to place
                for next_param in next_parameters:
                    if next_param.type == "position-variables":
                        bounded_args.setdefault(next_param.name, []).append(positional_arg)  # type: ignore
                else:
                    errors.append(PositionalAssignForKeyword(param, positional_arg))
                    continue
            elif param.type in ["position-variables"]:
                bounded_args.setdefault(param.name, []).append(positional_arg)  # type: ignore
                next_parameters.insert(0, param)
            else:
                if (
                    isinstance(self._options.reassignable, bool)
                    and not self._options.reassignable
                    or isinstance(self._options.reassignable, dict)
                    and not self._options.reassignable.get(param.name, False)
                ):
                    if param.name in bounded_args:
                        errors.append(ValueError(f"Parameter {param.name} already assigned"))
                        continue

                bounded_args[param.name] = positional_arg

        for name, value in kwargs.items():
            for param in next_parameters.copy():
                if param.name == name:
                    if param.type in ["position-only", "position-variables"]:
                        errors.append(KeywordAssignForPositional(param, value))
                    elif param.type in ["keyword-variables"]:
                        kwds = bounded_args.setdefault(name, {})  # type: ignore
                        kwds[name] = value  # type: ignore
                        next_parameters.remove(param)
                    else:
                        if (
                            isinstance(self._options.reassignable, bool)
                            and not self._options.reassignable
                            or isinstance(self._options.reassignable, dict)
                            and not self._options.reassignable.get(name, False)
                        ):
                            if name in bounded_args:
                                errors.append(ParameterAlreadyAssigned(param, bounded_args[name], value))
                                break
                        bounded_args[name] = value
                        next_parameters.remove(param)
                    break
            else:
                errors.append(KeywordParameterNotFound(name, value))

        if errors:
            raise SignatureErrorGroup(errors)

        return BindResult(self.signautre, next_parameters, bounded_args)

    def apply_defaults(self):
        """
        Apply default values to the parameters.

        Returns:
            BindResult: The bind result.
        """
        next_parameters = self.last_parameters.copy()
        bounded_args = self.bounded_args.copy()

        for param in next_parameters.copy():
            if param.default is not None and param.name not in bounded_args:
                bounded_args[param.name] = param.default
                next_parameters.remove(param)

        return BindResult(self.signautre, next_parameters, bounded_args)

    def complete(self):
        """
        Complete the binding process, checking if all required parameters are filled.

        Returns:
            BindResult: The bind result.

        Raises:
            SignatureErrorGroup: If there are errors in binding.
        """

        # check if all required parameters are filled
        errors = []

        for param in self.last_parameters:
            if param.type in {"position-only", "keyword-only", "positional-or-keyword"}:
                errors.append(MissingRequredParameter(param))

        if errors:
            raise SignatureErrorGroup(errors)

        return BindResult(self.signautre, self.last_parameters, self.bounded_args, True)

    def cbind(self, args: tuple[Value, ...], kwargs: dict[str, Value]):
        """
        Bind the signature with arguments, applying defaults and completing the binding process.

        Args:
            args (tuple[Value, ...]): Positional arguments.
            kwargs (dict[str, Value]): Keyword arguments.
        """
        return self.cbind_partial(args, kwargs).apply_defaults().complete()

    def bind_partial(self, *args: Value, **kwargs: Value):
        """
        Bind the signature with partial arguments, like a function call.

        Args:
            *args (Value): Positional arguments.
            **kwargs (Value): Keyword arguments.

        Returns:
            BindResult: The bind result.
        """
        return self.cbind_partial(args, kwargs)

    def bind(self, *args: Value, **kwargs: Value):
        """
        Bind the signature with arguments, like a function call.

        Args:
            *args (Value): Positional arguments.
            **kwargs (Value): Keyword arguments.

        Returns:
            BindResult: The bind result.
        """
        return self.cbind(args, kwargs)

    def options(self, opt: BindOptions):
        """
        Set the options for the binding process.

        Args:
            opt (BindOptions): The options.

        Returns:
            BindResult: The bind result.
        """
        return BindResult(self.signautre, self.last_parameters, self.bounded_args, self.completed, opt)

    def digest(self):
        """
        Return a signature that can be used to bind the remaining parameters.

        Returns:
            Signature: The signature.
        """
        return Signature(self.last_parameters)


class Signature:
    """
    Represents a signature of a function.
    
    Attributes:
        parameters (list[Parameter]): The parameters of the signature.
    """
    def __init__(self, parameters: list[Parameter]):
        self.parameters = parameters

    @property
    def empty_result(self):
        """
        Return an empty bind result that associates with this signature.

        Returns:
            BindResult: The bind result.
        """

        return BindResult(self, self.parameters.copy())

    def cbind_partial(self, args: tuple[Value, ...], kwargs: dict[str, Value]):
        """
        Bind the signature with partial arguments.

        Args:
            args (tuple[Value, ...]): Positional arguments.
            kwargs (dict[str, Value]): Keyword arguments.

        Returns:
            BindResult: The bind result.

        Raises:
            SignatureErrorGroup: If there are errors in binding.
        """
        return self.empty_result.cbind_partial(args, kwargs)

    def cbind(self, args: tuple[Value, ...], kwargs: dict[str, Value]):
        """
        Bind the signature with arguments, applying defaults and completing the binding process.

        Args:
            args (tuple[Value, ...]): Positional arguments.
            kwargs (dict[str, Value]): Keyword arguments.

        Returns:
            BindResult: The bind result.

        Raises:
            SignatureErrorGroup: If there are errors in binding.
        """
        return self.empty_result.cbind(args, kwargs)

    def bind_partial(self, *args: Value, **kwargs: Value):
        """
        Bind the signature with partial arguments, like a function call.

        Args:
            *args (Value): Positional arguments.
            **kwargs (Value): Keyword arguments.

        Returns:
            BindResult: The bind result.
        """
        return self.cbind_partial(args, kwargs)

    def bind(self, *args: Value, **kwargs: Value):
        """
        Bind the signature with arguments, like a function call.

        Args:
            *args (Value): Positional arguments.
            **kwargs (Value): Keyword arguments.

        Returns:
            BindResult: The bind result.
        """
    
        return self.cbind(args, kwargs)

    def options(self, opt: BindOptions):
        """
        Set the options for the binding process.

        Args:
            opt (BindOptions): The options.

        Returns:
            BindResult: The bind result.
        """

        return self.empty_result.options(opt)

    def check_valid(self, *, return_errors: bool = False) -> SignatureErrorGroup | None:
        """
        Check if the signature is valid: whether the parameters follow the python rules.
        The rules could be found in the python documentation.

        Args:
            return_errors (bool): Whether to return the errors instead of raising them.

        Returns:
            SignatureErrorGroup | None: The errors if `return_errors` is True, otherwise None.

        Raises:
            SignatureErrorGroup: If there are errors in the signature.
        """

        # check if the parameters follows python rules
        # rules: [...positional-only], /, [positional-or-keyword], [*position-variables / *], [keyword-only], [**keyword-variables]
        errors = []
        last_role: ParameterType = "position-only"
        prev_args = []
        positional_var_found = False
        keyword_var_found = False

        for i in self.parameters:
            if i.name in prev_args:
                errors.append(DuplicatedParameterName(i.name, [i for i in self.parameters if i.name == i.name]))
                continue

            prev_args.append(i.name)

            if i.type == "position-variables" and positional_var_found:
                errors.append(MultiplePositionalVariablesParameter([i for i in self.parameters if i.type == "position-variables"]))

            if i.type == "keyword-variables" and keyword_var_found:
                errors.append(MultipleKeywordVariablesParameter([i for i in self.parameters if i.type == "keyword-variables"]))

            if last_role == "positional-or-keyword":
                if i.type == "position-only":
                    errors.append(ParameterMisplaced("positional-or-keyword", i))
                    continue

            elif last_role == "position-variables":
                if i.type in {"keyword-only", "keyword-variables"}:
                    errors.append(ParameterMisplaced("position-variables", i))
                    continue

            elif last_role == "keyword-only":
                if i.type not in {"keyword-only", "keyword-variables"}:
                    errors.append(ParameterMisplaced("keyword-only", i))
                    continue

            elif last_role == "keyword-variables":
                errors.append(ParameterMisplaced("keyword-variables", i))
                continue

            last_role = i.type

        if errors:
            group = SignatureErrorGroup(errors)
            if return_errors:
                return group
            raise group

    @classmethod
    def from_runtime(cls, signature: RuntimeSignature):
        """
        Create a signature from [`inspect.Signature`].
        
        Args:
            signature ([`inspect.Signature`]): The signature.

        Returns:
            Signature: The signature.
        """

        parameters = []

        for param in signature.parameters.values():
            parameters.append(
                Parameter(param.name, param.annotation, param.default, PARAMETER_TYPES_CAST_MAP[param.kind])
            )  # TODO: proper cast to Value

        return cls(parameters)

    @classmethod
    def from_callable(cls, func):
        """
        Create a signature from a callable object.

        Args:
            func (callable): The callable object.

        Returns:
            Signature: The signature.
        """

        return cls.from_runtime(RuntimeSignature.from_callable(func))

    def __str__(self):
        """
        Return the string representation of the signature.
        
        Returns:
            str: The string representation.
        """

        # rules: [...positional-only, /], [positional-or-keyword], [*args / *], [keyword-only], [**kwargs]
        g = dict([(k, list(v)) for k, v in groupby(self.parameters, key=lambda x: x.type)])

        if "position-only" in g:
            position_only = ", ".join(map(str, g["position-only"]))
        else:
            position_only = ""

        position_or_keyword = ", ".join(map(str, g.get("positional-or-keyword", [])))
        position_variables = ", ".join(map(str, g.get("position-variables", [])))

        if "keyword-only" in g:
            keyword_only = ", ".join(map(str, g["keyword-only"]))
        else:
            keyword_only = ""

        if "keyword-variables" in g:
            keyword_variables = ", ".join(map(str, g["keyword-variables"]))
        else:
            keyword_variables = ""

        result = ""

        if position_only:
            result += f"{position_only}, /"

        if result:
            result += ", "
        result += position_or_keyword

        if position_variables:
            if result:
                result += ", "
            result += position_variables

        if keyword_only:
            if result:
                result += ", "
            result += keyword_only

        if keyword_variables:
            if result:
                result += ", "
            result += keyword_variables

        return f"({result})"
