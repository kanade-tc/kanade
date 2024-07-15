from __future__ import annotations

from dataclasses import dataclass
from tree_sitter import Tree, Node


@dataclass
class PyItem:
    ast_node: Node

@dataclass
class PyModule(PyItem):
    ast_tree: Tree