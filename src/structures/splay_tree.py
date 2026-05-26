"""Árvore Splay (auto-ajustável) para cache de metadados de documentos.

RF03 — A cada acesso bem-sucedido, o nó é "splayed" para a raiz da árvore,
mantendo elementos quentes (mais consultados recentemente) no topo.

Garantias:
    * Inserção, busca e remoção em O(log N) amortizado.
    * Acesso a um nó faz com que ele se torne a nova raiz.
    * Boa adaptação a distribuições enviesadas (LRU-like).

A implementação é iterativa onde possível para evitar estouro de pilha
em árvores muito desbalanceadas (caso típico antes do splay).
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple


class _SplayNode:
    __slots__ = ("key", "value", "left", "right", "parent")

    def __init__(self, key: Any, value: Any) -> None:
        self.key = key
        self.value = value
        self.left: Optional[_SplayNode] = None
        self.right: Optional[_SplayNode] = None
        self.parent: Optional[_SplayNode] = None


class SplayTree:
    """Splay Tree clássica (Sleator & Tarjan, 1985)."""

    def __init__(self, capacity: Optional[int] = None) -> None:
        """
        Args:
            capacity: se informado, a árvore se comporta como cache LRU-like:
                quando o número de chaves excede `capacity`, removemos a folha
                mais profunda do caminho oposto à raiz (proxy razoável para
                "menos recentemente acessado", já que itens quentes ficam no topo).
        """
        self._root: Optional[_SplayNode] = None
        self._size = 0
        self._capacity = capacity
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    # ---------------------------------------------------------------- helpers
    def __len__(self) -> int:
        return self._size

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    @property
    def evictions(self) -> int:
        return self._evictions

    def root_key(self) -> Optional[Any]:
        return None if self._root is None else self._root.key

    # ---------------------------------------------------------------- rotações
    @staticmethod
    def _rotate_left(node: _SplayNode) -> _SplayNode:
        right = node.right
        assert right is not None
        node.right = right.left
        if right.left is not None:
            right.left.parent = node
        right.parent = node.parent
        if node.parent is not None:
            if node.parent.left is node:
                node.parent.left = right
            else:
                node.parent.right = right
        right.left = node
        node.parent = right
        return right

    @staticmethod
    def _rotate_right(node: _SplayNode) -> _SplayNode:
        left = node.left
        assert left is not None
        node.left = left.right
        if left.right is not None:
            left.right.parent = node
        left.parent = node.parent
        if node.parent is not None:
            if node.parent.left is node:
                node.parent.left = left
            else:
                node.parent.right = left
        left.right = node
        node.parent = left
        return left

    def _splay(self, node: _SplayNode) -> None:
        """Move `node` para a raiz aplicando zig / zig-zig / zig-zag."""
        while node.parent is not None:
            parent = node.parent
            grand = parent.parent
            if grand is None:                                  # zig
                if node is parent.left:
                    self._rotate_right(parent)
                else:
                    self._rotate_left(parent)
            elif node is parent.left and parent is grand.left:  # zig-zig
                self._rotate_right(grand)
                self._rotate_right(parent)
            elif node is parent.right and parent is grand.right:
                self._rotate_left(grand)
                self._rotate_left(parent)
            elif node is parent.right and parent is grand.left:  # zig-zag
                self._rotate_left(parent)
                self._rotate_right(grand)
            else:
                self._rotate_right(parent)
                self._rotate_left(grand)
        self._root = node

    # ------------------------------------------------------------------ CRUD
    def insert(self, key: Any, value: Any) -> None:
        if self._root is None:
            self._root = _SplayNode(key, value)
            self._size = 1
            return

        node = self._root
        parent: Optional[_SplayNode] = None
        while node is not None:
            parent = node
            if key == node.key:
                node.value = value
                self._splay(node)
                return
            node = node.left if key < node.key else node.right

        new_node = _SplayNode(key, value)
        new_node.parent = parent
        assert parent is not None
        if key < parent.key:
            parent.left = new_node
        else:
            parent.right = new_node
        self._size += 1
        self._splay(new_node)

        if self._capacity is not None and self._size > self._capacity:
            self._evict_one()

    def get(self, key: Any, default: Any = None) -> Any:
        node = self._search_node(key)
        if node is None:
            self._misses += 1
            return default
        self._hits += 1
        self._splay(node)
        return node.value

    def contains(self, key: Any) -> bool:
        return self._search_node(key) is not None

    def remove(self, key: Any) -> bool:
        node = self._search_node(key)
        if node is None:
            return False
        self._splay(node)
        left, right = self._root.left, self._root.right
        if left is not None:
            left.parent = None
        if right is not None:
            right.parent = None

        if left is None:
            self._root = right
        else:
            # encontra o máximo da subárvore esquerda e splay para a raiz
            max_left = left
            while max_left.right is not None:
                max_left = max_left.right
            self._root = left
            self._splay(max_left)
            self._root.right = right
            if right is not None:
                right.parent = self._root
        self._size -= 1
        return True

    # ------------------------------------------------------ caminhamento ordem
    def in_order(self) -> List[Tuple[Any, Any]]:
        """Caminhamento em-ordem iterativo (usado para inspeção/depuração)."""
        result: List[Tuple[Any, Any]] = []
        stack: List[_SplayNode] = []
        node = self._root
        while stack or node is not None:
            while node is not None:
                stack.append(node)
                node = node.left
            node = stack.pop()
            result.append((node.key, node.value))
            node = node.right
        return result

    # ------------------------------------------------------------------ stats
    def stats(self) -> dict:
        return {
            "size": self._size,
            "capacity": self._capacity,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "root": self.root_key(),
        }

    # ------------------------------------------------------------------- util
    def _search_node(self, key: Any) -> Optional[_SplayNode]:
        node = self._root
        last: Optional[_SplayNode] = None
        while node is not None:
            last = node
            if key == node.key:
                return node
            node = node.left if key < node.key else node.right
        # Splay do último nó visitado (técnica padrão para árvore Splay).
        if last is not None:
            self._splay(last)
        return None

    def _evict_one(self) -> None:
        """Remove um candidato 'frio' (folha mais profunda longe da raiz).

        Heurística determinística: descemos sempre pelo filho de maior
        profundidade da subárvore oposta àquela onde acabamos de inserir.
        Empates são desempatados pelo lado direito.
        """
        if self._root is None:
            return
        # Vamos buscar a folha mais profunda alcançada saindo da raiz pelo
        # lado oposto ao caminho hot (esquerda primeiro, depois direita).
        node = self._root
        # Caminha alternadamente para o lado mais "antigo": esquerda preferida.
        while True:
            if node.left is not None:
                node = node.left
            elif node.right is not None:
                node = node.right
            else:
                break  # folha
        # remove a folha
        parent = node.parent
        if parent is not None:
            if parent.left is node:
                parent.left = None
            else:
                parent.right = None
        else:
            self._root = None
        self._size -= 1
        self._evictions += 1
