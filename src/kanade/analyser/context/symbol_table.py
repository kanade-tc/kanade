from __future__ import annotations

from collections import ChainMap
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from kanade.analyser.globals import SYMBOL_TABLE
from kanade.analyser.utils import lazy


@dataclass
class SymbolTableFrame:
    symbols: dict[str, Any] = field(default_factory=dict)  # TODO: proper type


@dataclass
class SymbolTableSlice:
    table: SymbolTable
    offset: int | None
    frames: list[SymbolTableFrame]

    @lazy
    def map(self):
        return ChainMap(*[frame.symbols for frame in self.frames])

    def __getitem__(self, key: str):
        return self.map[key]


@dataclass
class SymbolTable:
    frames: list[SymbolTableFrame] = field(default_factory=list)

    parent: SymbolTable | None = None
    parent_offset: int | None = None

    def __getitem__(self, offset: int | None = None):
        ret = self.frames[::-1][:offset]
        if self.parent is not None:
            ret.extend(self.parent[self.parent_offset].frames)

        return SymbolTableSlice(self, offset, ret)

    @contextmanager
    def scope(self):
        token = SYMBOL_TABLE.set(self)
        try:
            yield self
        finally:
            SYMBOL_TABLE.reset(token)
    
    def new_table(self, offset: int | None = None) -> SymbolTable:
        return SymbolTable(frames=[], parent=self, parent_offset=offset)

    def push_frame(self, frame: SymbolTableFrame):
        self.frames.append(frame)
