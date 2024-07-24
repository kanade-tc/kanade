from __future__ import annotations

from typing import TYPE_CHECKING
from contextvars import ContextVar

if TYPE_CHECKING:
    from kanade.analyser.context.symbol_table import SymbolTable

SYMBOL_TABLE: ContextVar[SymbolTable] = ContextVar('SYMBOL_TABLE')