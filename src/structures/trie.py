"""Árvore Trie (prefix tree) com autocompletar via DFS.

RF02 — Vocabulário do Motor RAG.

Complexidades (L = comprimento da chave, K = limite de sugestões):
    insert(word)            -> O(L)
    contains(word)          -> O(L)
    starts_with(prefix)     -> O(L)
    autocomplete(prefix, K) -> O(L + S), onde S é o número de nós visitados
                               na sub-árvore (limitado por poda quando K é atingido)

A árvore representa cada filho como uma HashTable própria, evitando o
uso do dict nativo do Python na lógica central da estrutura.
"""

from __future__ import annotations

from typing import List, Optional

from .hash_table import HashTable


class _TrieNode:
    __slots__ = ("children", "is_word", "frequency", "char")

    def __init__(self, char: str = "") -> None:
        self.children: HashTable = HashTable(capacity=8)
        self.is_word: bool = False
        self.frequency: int = 0
        self.char: str = char


class Trie:
    def __init__(self) -> None:
        self._root = _TrieNode()
        self._size = 0

    def __len__(self) -> int:
        return self._size

    # ------------------------------------------------------- core operations
    def insert(self, word: str, frequency_increment: int = 1) -> None:
        if not word:
            return
        node = self._root
        for ch in word:
            child: Optional[_TrieNode] = node.children.get(ch)
            if child is None:
                child = _TrieNode(ch)
                node.children.put(ch, child)
            node = child
        if not node.is_word:
            self._size += 1
        node.is_word = True
        node.frequency += frequency_increment

    def contains(self, word: str) -> bool:
        node = self._find_node(word)
        return node is not None and node.is_word

    def starts_with(self, prefix: str) -> bool:
        return self._find_node(prefix) is not None

    def frequency_of(self, word: str) -> int:
        node = self._find_node(word)
        if node is None or not node.is_word:
            return 0
        return node.frequency

    # ----------------------------------------------------------- autocomplete
    def autocomplete(self, prefix: str, limit: int = 10) -> List[str]:
        """Retorna até `limit` palavras que começam com `prefix`.

        A busca utiliza DFS iterativa para evitar estouro de pilha
        em prefixos longos. As sugestões são ordenadas dentro do motor
        RAG (por frequência) — aqui devolvemos em ordem lexicográfica
        determinística (ordenação dos filhos por caractere durante a DFS).
        """
        if limit <= 0:
            return []
        start = self._find_node(prefix)
        if start is None:
            return []

        results: List[str] = []
        # Pilha de tuplas (node, caminho_atual)
        stack: List = [(start, prefix)]
        while stack and len(results) < limit:
            node, path = stack.pop()
            if node.is_word:
                results.append(path)
                if len(results) >= limit:
                    break
            # Ordena filhos por caractere para garantir saída determinística.
            children_sorted = sorted(node.children.items(), key=lambda kv: kv[0])
            # Empilhamos invertido para que a DFS visite os menores primeiro.
            for ch, child in reversed(children_sorted):
                stack.append((child, path + ch))
        return results

    def autocomplete_with_frequency(self, prefix: str, limit: int = 10):
        """Como autocomplete(), mas devolve (palavra, frequência).

        Usado pelo motor RAG para priorizar termos mais relevantes.
        Lê TODAS as palavras com aquele prefixo (sem limite intermediário)
        e a ordenação final fica a cargo do chamador (HeapSort externo).
        """
        start = self._find_node(prefix)
        if start is None:
            return []

        results: List = []
        stack: List = [(start, prefix)]
        while stack:
            node, path = stack.pop()
            if node.is_word:
                results.append((path, node.frequency))
            children_sorted = sorted(node.children.items(), key=lambda kv: kv[0])
            for ch, child in reversed(children_sorted):
                stack.append((child, path + ch))
            if limit and len(results) >= limit * 10:
                # Pequena salvaguarda: paramos depois de coletar 10x o
                # limit pedido pelo usuário. O motor RAG ainda fará a
                # ordenação final (HeapSort) sobre esse pool.
                break
        return results

    # ----------------------------------------------------------- estatísticas
    def stats(self) -> dict:
        node_count = 0
        max_depth = 0
        stack = [(self._root, 0)]
        while stack:
            node, depth = stack.pop()
            node_count += 1
            if depth > max_depth:
                max_depth = depth
            for _, child in node.children.items():
                stack.append((child, depth + 1))
        return {
            "words": self._size,
            "nodes": node_count,
            "max_depth": max_depth,
        }

    # ----------------------------------------------------------------- utils
    def _find_node(self, key: str) -> Optional[_TrieNode]:
        node = self._root
        for ch in key:
            child = node.children.get(ch)
            if child is None:
                return None
            node = child
        return node
