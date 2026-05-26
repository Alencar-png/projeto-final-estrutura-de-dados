"""Índice invertido em memória, construído sobre HashTable própria.

RF01 — Mapeia termos -> postings list (doc_id -> frequência do termo).

Internamente cada posting é também uma HashTable[doc_id -> count],
mantendo todas as operações de inserção e consulta em O(1) amortizado.
"""

from __future__ import annotations

from typing import Iterable, Iterator, List, Tuple

from .hash_table import HashTable


class InvertedIndex:
    """Índice invertido: termo -> {doc_id: term_frequency}."""

    def __init__(self) -> None:
        self._index: HashTable = HashTable()
        self._doc_lengths: HashTable = HashTable()   # doc_id -> qtde de termos
        self._total_docs: int = 0
        self._known_docs: HashTable = HashTable()    # doc_id -> True

    # ------------------------------------------------------------- inserção
    def add_document(self, doc_id: str, tokens: Iterable[str]) -> None:
        if not self._known_docs.get(doc_id, False):
            self._known_docs.put(doc_id, True)
            self._total_docs += 1

        length = 0
        for token in tokens:
            length += 1
            postings: HashTable = self._index.get_or_create(token, HashTable)
            current = postings.get(doc_id, 0)
            postings.put(doc_id, current + 1)
        # Acumula tamanho do documento (permite docs em chunks no futuro).
        previous = self._doc_lengths.get(doc_id, 0)
        self._doc_lengths.put(doc_id, previous + length)

    # ------------------------------------------------------------- consultas
    def term_frequency(self, term: str, doc_id: str) -> int:
        postings = self._index.get(term)
        if postings is None:
            return 0
        return postings.get(doc_id, 0)

    def document_frequency(self, term: str) -> int:
        postings: HashTable = self._index.get(term)
        return 0 if postings is None else len(postings)

    def postings(self, term: str) -> Iterator[Tuple[str, int]]:
        postings: HashTable = self._index.get(term)
        if postings is None:
            return iter(())
        return postings.items()

    def doc_length(self, doc_id: str) -> int:
        return self._doc_lengths.get(doc_id, 0)

    @property
    def total_docs(self) -> int:
        return self._total_docs

    @property
    def vocabulary_size(self) -> int:
        return len(self._index)

    def vocabulary(self) -> Iterator[str]:
        return self._index.keys()

    def stats(self) -> dict:
        return {
            "vocabulary": self.vocabulary_size,
            "documents": self._total_docs,
            "hash_index": self._index.stats(),
        }
