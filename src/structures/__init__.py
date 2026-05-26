"""Implementações manuais das estruturas de dados centrais.

Nenhuma destas estruturas utiliza bibliotecas de alto nível
(dict/list de Python são usadas apenas como buffers auxiliares,
NUNCA como substituto da estrutura exigida).
"""

from .hash_table import HashTable
from .inverted_index import InvertedIndex
from .trie import Trie
from .splay_tree import SplayTree
from .heap_sort import heap_sort, top_k

__all__ = [
    "HashTable",
    "InvertedIndex",
    "Trie",
    "SplayTree",
    "heap_sort",
    "top_k",
]
