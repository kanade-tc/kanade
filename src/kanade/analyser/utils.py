from __future__ import annotations
import asyncio
from typing import Any, Callable, Generic, Self, TypeVar, Awaitable, overload

from awaitlet import awaitlet


_T = TypeVar("_T")
_R_co = TypeVar("_R_co", covariant=True)

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class future_property(Generic[_T, _R_co]):
    def __init__(self, fget: Callable[[_T], Awaitable[_R_co]]):
        self.fget = fget

    @overload
    def __get__(self, instance: None, owner: type | None = None) -> Self: ...
    @overload
    def __get__(self, instance: _T, owner: type[_T]) -> _R_co: ...

    def __get__(self, instance: _T | None, owner: type[_T] | None = None) -> _R_co | Self:
        if instance is None:
            return self

        return awaitlet(self.fget(instance))


class waitslot(Generic[_T]):
    def __init__(self):
        ...

    def __set_name__(self, owner: type, name: str) -> None:
        setattr(owner, name, asyncio.Future())
        self.__name__ = name

    @overload
    def __get__(self, instance: None, owner: type | None = None) -> Self: ...
    @overload
    def __get__(self, instance: Any, owner: type) -> _T: ...

    def __get__(self, instance: Any | None, owner: type | None = None) -> _T | Self:
        if instance is None:
            return self

        return awaitlet(getattr(instance, self.__name__))

    def __set__(self, instance: Any, value: _T) -> None:
        fut: asyncio.Future = getattr(instance, self.__name__)
        fut.set_result(value)
    
    def __delete__(self, instance: Any) -> None:
        setattr(instance, self.__name__, asyncio.Future())


class lazy(Generic[_T]):
    def __init__(self, fn: Callable[[Any], _T]):
        self.fn = fn
    
    def __set_name__(self, owner: type, name: str) -> None:
        self.__name__ = name
    
    @overload
    def __get__(self, instance: None, owner: type | None = None) -> Self: ...
    @overload
    def __get__(self, instance: Any, owner: type) -> _T: ...
    def __get__(self, instance: Any | None, owner: type | None = None) -> _T | Self:
        if instance is None:
            return self
        
        if not hasattr(instance, self.__name__):
            value = self.fn(instance)
            setattr(instance, self.__name__, value)
        else:
            value = getattr(instance, self.__name__)

        return value