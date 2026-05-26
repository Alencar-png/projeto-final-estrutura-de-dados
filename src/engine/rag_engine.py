"""Orquestrador do Motor RAG Local.

Integra todas as estruturas implementadas:
    * RF01 - HashTable + InvertedIndex .... busca textual / scoring TF-IDF
    * RF02 - Trie ......................... autocompletar (DFS)
    * RF03 - SplayTree .................... cache de metadados acessados
    * RF04 - HeapSort / top_k ............. Top-K por relevância

A operação SEARCH usa TF-IDF clássico:

    score(doc, q) = SUM_{t in q}  tf(t, doc) * idf(t)
    idf(t)        = log( (1 + N) / (1 + df(t)) ) + 1
    tf(t, doc)    = count(t, doc) / max(1, doc_len(doc))

O resultado final é ordenado via heap_sort externo (RF04) garantindo
O(N log N) no pior caso, e retorna o Top-K via uma min-heap de tamanho K.

Determinismo: empates de score são desempatados por doc_id em ordem
lexicográfica crescente.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from ..structures import (
    HashTable,
    InvertedIndex,
    SplayTree,
    Trie,
    heap_sort,
    top_k,
)
from .tokenizer import tokenize


class RAGEngine:
    def __init__(self, splay_capacity: Optional[int] = 256) -> None:
        self.index = InvertedIndex()
        self.trie = Trie()
        self.cache = SplayTree(capacity=splay_capacity)

        # Metadados completos vivem em uma HashTable separada — o Splay
        # guarda apenas o subconjunto "quente" / recentemente acessado.
        self._documents: HashTable = HashTable()

    # ============================================================== ingestão
    def ingest_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Indexa uma lista de documentos.

        Cada documento aceito tem o formato:
            {
                "id": str (obrigatório),
                "titulo": str (opcional),
                "conteudo": str (opcional),
                "metadados": dict (opcional)
            }
        """
        for doc in documents:
            doc_id = doc.get("id")
            if not isinstance(doc_id, str) or not doc_id:
                raise ValueError("Cada documento precisa de um 'id' não-vazio (string).")

            text_pieces: List[str] = []
            if isinstance(doc.get("titulo"), str):
                text_pieces.append(doc["titulo"])
            if isinstance(doc.get("conteudo"), str):
                text_pieces.append(doc["conteudo"])

            tokens = []
            for piece in text_pieces:
                tokens.extend(tokenize(piece))

            self.index.add_document(doc_id, tokens)

            # Atualiza a Trie de vocabulário (RF02) somando frequências
            # globais por termo, permitindo ranking por relevância.
            for tk in tokens:
                self.trie.insert(tk, frequency_increment=1)

            # Armazena o documento completo em uma HashTable (não o Splay).
            self._documents.put(doc_id, doc)

    # ============================================================== queries
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Devolve os Top-K documentos mais relevantes para `query`."""
        terms = tokenize(query)
        if not terms:
            return []

        scores: HashTable = HashTable()  # doc_id -> score acumulado
        N = max(1, self.index.total_docs)
        for term in terms:
            df = self.index.document_frequency(term)
            if df == 0:
                continue
            idf = math.log((1 + N) / (1 + df)) + 1
            for doc_id, tf_count in self.index.postings(term):
                doc_len = max(1, self.index.doc_length(doc_id))
                tf = tf_count / doc_len
                current = scores.get(doc_id, 0.0)
                scores.put(doc_id, current + tf * idf)

        if len(scores) == 0:
            return []

        # Constrói uma lista de tuplas (score, doc_id) e usa Top-K via heap.
        # IMPORTANTE: para desempate determinístico por doc_id ASC, usamos
        # a chave (score, -ord_chave) — simplificamos com truque abaixo.
        candidates = list(scores.items())  # [(doc_id, score)]

        # Top-K maiores por score:
        top = top_k(
            candidates,
            k,
            key=lambda kv: kv[1],
            reverse=True,
        )

        # Resolve empates: ordena os K resultados por (-score, doc_id ASC)
        # usando heap_sort sobre uma lista pequena (K <= 5 tipicamente).
        # Como heap_sort ordena ascendente por default, usamos uma chave
        # composta que respeita o desempate desejado.
        # Como queremos score DESC + doc_id ASC, transformamos em uma
        # chave única usando uma tupla (score, doc_id) e ordenamos com
        # reverse=False sobre chave invertida.
        # Implementação direta:
        from ..structures.heap_sort import heap_sort as _hs
        _hs(top, key=lambda kv: (-kv[1], kv[0]), reverse=False)

        results: List[Dict[str, Any]] = []
        for doc_id, score in top:
            metadata = self._touch_cache(doc_id)
            results.append(
                {
                    "doc_id": doc_id,
                    "score": round(score, 6),
                    "titulo": (metadata or {}).get("titulo", ""),
                }
            )
        return results

    def autocomplete(self, prefix: str, limit: int = 10) -> List[str]:
        """RF02 — usa DFS sobre a Trie, ordena por frequência via HeapSort."""
        if not prefix:
            return []
        from .tokenizer import _strip_accents
        prefix = _strip_accents(prefix).lower()
        pool = self.trie.autocomplete_with_frequency(prefix, limit=limit)
        if not pool:
            return []
        # Ordena por (-frequência, palavra ASC) usando heap_sort.
        heap_sort(pool, key=lambda wf: (-wf[1], wf[0]), reverse=False)
        return [w for w, _ in pool[:limit]]

    def cache_get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """RF03 — acesso explícito ao cache de metadados (splay)."""
        return self._touch_cache(doc_id)

    def cache_status(self) -> Dict[str, Any]:
        return self.cache.stats()

    # ============================================================== internos
    def _touch_cache(self, doc_id: str) -> Optional[Dict[str, Any]]:
        cached = self.cache.get(doc_id)
        if cached is not None:
            return cached
        full = self._documents.get(doc_id)
        if full is None:
            return None
        # Insere apenas os metadados essenciais no Splay.
        light = {
            "id": full.get("id"),
            "titulo": full.get("titulo", ""),
            "metadados": full.get("metadados", {}),
        }
        self.cache.insert(doc_id, light)
        return light

    # ============================================================== métricas
    def stats(self) -> Dict[str, Any]:
        return {
            "indice_invertido": self.index.stats(),
            "trie": self.trie.stats(),
            "cache_splay": self.cache.stats(),
        }
